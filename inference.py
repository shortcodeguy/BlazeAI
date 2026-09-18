"""
BlazeAI v5 - Streaming Inference Engine
Created by ShortCodeGuy Studio

Executes real-time, token-by-token streaming inference using KV caching
and CPU-optimized generation. Records accurate latency and throughput metrics.
Contains ZERO domain knowledge.
"""

import threading
import time
from typing import Callable, Generator, Optional, Tuple
import torch
from transformers import TextIteratorStreamer

from config import generation_config, system_config
from benchmark import TurnMetrics, get_current_ram_mb, get_system_ram_info, session_benchmark
from conversation import ConversationManager
from model import ModelManager


class InferenceEngine:
    """Handles model tokenization, prompt encoding, and streaming text generation."""

    def __init__(self):
        self.model_manager = ModelManager.get_instance()

    def stream_generate(
        self,
        conversation_manager: ConversationManager,
        user_input: str,
        on_token_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[str, TurnMetrics]:
        """
        Runs streaming generation for the user's prompt.
        Streams text tokens in real time via on_token_callback / generator,
        and returns the full generated assistant response along with real turn metrics.
        """
        model, tokenizer = self.model_manager.load_model()

        # Context trimming to guarantee context window limits
        conversation_manager.trim_context(tokenizer, max_tokens=system_config.max_context_tokens)

        # Build standard chat messages
        messages = conversation_manager.get_messages(user_input)

        # Tokenize prompt using the model's native chat template
        prompt_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = tokenizer(prompt_text, return_tensors="pt")
        input_ids = inputs["input_ids"]
        prompt_tokens_count = input_ids.shape[-1]

        # Setup streamer for token-by-token output
        streamer = TextIteratorStreamer(
            tokenizer,
            timeout=120.0,
            skip_prompt=True,
            skip_special_tokens=True
        )

        # Generation kwargs with KV cache enabled
        gen_kwargs = {
            "input_ids": input_ids,
            "attention_mask": inputs.get("attention_mask"),
            "max_new_tokens": generation_config.max_new_tokens,
            "temperature": generation_config.temperature if generation_config.do_sample else None,
            "top_p": generation_config.top_p if generation_config.do_sample else None,
            "top_k": generation_config.top_k if generation_config.do_sample else None,
            "repetition_penalty": generation_config.repetition_penalty,
            "do_sample": generation_config.do_sample,
            "use_cache": True,  # KV cache optimization
            "streamer": streamer,
            "pad_token_id": tokenizer.eos_token_id,
        }

        # Clean None values
        gen_kwargs = {k: v for k, v in gen_kwargs.items() if v is not None}

        # Timing and latency tracking
        t_start = time.perf_counter()
        t_first_token: Optional[float] = None
        generated_chunks: list[str] = []

        # Run model.generate in a separate worker thread for seamless streaming
        generation_thread = threading.Thread(
            target=model.generate,
            kwargs=gen_kwargs
        )
        generation_thread.daemon = True
        generation_thread.start()

        # Stream tokens live as they are produced by the model
        for new_text in streamer:
            if t_first_token is None:
                t_first_token = time.perf_counter()
            generated_chunks.append(new_text)
            if on_token_callback:
                on_token_callback(new_text)

        generation_thread.join()
        t_end = time.perf_counter()

        full_response = "".join(generated_chunks).strip()

        # Compute real benchmarks
        ttft_sec = (t_first_token - t_start) if t_first_token else (t_end - t_start)
        total_time_sec = t_end - t_start
        gen_time_sec = (t_end - t_first_token) if t_first_token else total_time_sec

        # Count actual generated tokens using the tokenizer
        response_tokens = tokenizer(full_response, return_tensors="pt")["input_ids"].shape[-1]
        tokens_per_sec = (response_tokens / gen_time_sec) if gen_time_sec > 0 else 0.0
        prompt_tokens_per_sec = (prompt_tokens_count / ttft_sec) if ttft_sec > 0 else 0.0

        proc_ram = get_current_ram_mb()
        sys_ram = get_system_ram_info()

        metrics = TurnMetrics(
            prompt_tokens=prompt_tokens_count,
            generated_tokens=response_tokens,
            total_tokens=prompt_tokens_count + response_tokens,
            time_to_first_token_sec=ttft_sec,
            generation_time_sec=gen_time_sec,
            total_latency_sec=total_time_sec,
            tokens_per_sec=tokens_per_sec,
            prompt_tokens_per_sec=prompt_tokens_per_sec,
            process_ram_mb=proc_ram,
            system_ram_percent=sys_ram["percent"]
        )

        session_benchmark.record_turn(metrics)

        # Update conversation history with the real model response
        conversation_manager.add_user_message(user_input)
        conversation_manager.add_assistant_message(full_response)

        return full_response, metrics
