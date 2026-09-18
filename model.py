"""
BlazeAI v5 - Model Lifecycle Management
Created by ShortCodeGuy Studio

Loads and holds the instruct language model and tokenizer in memory.
Applies CPU thread optimizations and low memory footprint configurations.
Contains ZERO domain knowledge.
"""

import gc
import os
import time
from typing import Optional, Tuple
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, PreTrainedModel, PreTrainedTokenizer

from config import system_config
from benchmark import session_benchmark


class ModelManager:
    """Manages the lifecycle, loading, and memory of the language model."""

    _instance: Optional["ModelManager"] = None

    def __init__(self):
        self.model_id: str = ""
        self.model: Optional[PreTrainedModel] = None
        self.tokenizer: Optional[PreTrainedTokenizer] = None
        self.load_time_sec: float = 0.0

    @classmethod
    def get_instance(cls) -> "ModelManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def configure_cpu_threads(self):
        """Optimizes PyTorch CPU execution threads for hardware."""
        threads = system_config.cpu_threads
        torch.set_num_threads(threads)
        # Suppress unnecessary HF symlink warnings on Windows
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

    def load_model(self, model_id: Optional[str] = None) -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
        """
        Loads the instruct model and tokenizer into memory.
        If already loaded with the same model_id, returns existing instances.
        """
        target_model = model_id or system_config.default_model_id

        if self.model is not None and self.tokenizer is not None and self.model_id == target_model:
            return self.model, self.tokenizer

        # If switching model, free existing memory first
        if self.model is not None:
            del self.model
            del self.tokenizer
            self.model = None
            self.tokenizer = None
            gc.collect()

        self.configure_cpu_threads()

        t_start = time.perf_counter()
        
        # Load Tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            target_model,
            trust_remote_code=True
        )

        # Select data type
        torch_dtype = torch.bfloat16 if system_config.dtype == "bfloat16" else torch.float32

        # Load Model with CPU optimization
        model = AutoModelForCausalLM.from_pretrained(
            target_model,
            dtype=torch_dtype,
            low_cpu_mem_usage=True,
            trust_remote_code=True
        )
        model.eval()

        self.load_time_sec = time.perf_counter() - t_start
        self.model_id = target_model
        self.model = model
        self.tokenizer = tokenizer

        # Update session benchmark
        session_benchmark.model_name = target_model
        session_benchmark.model_load_time_sec = self.load_time_sec

        return self.model, self.tokenizer

    def get_model_info(self) -> dict:
        """Returns metadata about the active loaded model."""
        if self.model is None:
            return {"status": "Not loaded"}
            
        param_count = sum(p.numel() for p in self.model.parameters())
        return {
            "model_id": self.model_id,
            "parameters": f"{param_count / 1e6:.1f}M" if param_count < 1e9 else f"{param_count / 1e9:.2f}B",
            "load_time": f"{self.load_time_sec:.2f}s",
            "device": str(self.model.device),
            "dtype": str(self.model.dtype),
            "threads": torch.get_num_threads(),
        }
