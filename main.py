"""
BlazeAI v5 - Main Terminal Interface
Created by ShortCodeGuy Studio

Terminal-based real local AI chatbot.
Zero hardcoded AI responses, answers, or knowledge.
All conversation is powered by a real, locally loaded instruct language model.
"""

import sys
import time
from typing import Optional

from config import generation_config, system_config
from conversation import ConversationManager
from model import ModelManager
from inference import InferenceEngine
from benchmark import session_benchmark


BANNER = r"""
============================================================
                         BlazeAI v5                         
               Created by ShortCodeGuy Studio               
============================================================
"""


def print_help():
    """Displays available application commands."""
    print("\n[Application Commands]")
    print("  /help                     Show this help message")
    print("  /clear                    Clear current conversation history")
    print("  /model                    Show active model specifications")
    print("  /model <name>             Switch to a different local model")
    print("  /stats                    Display detailed session benchmarks & RAM")
    print("  /settings                 View current generation parameters")
    print("  /settings <param> <val>   Update parameter (e.g. /settings temperature 0.8)")
    print("  /save [filename]          Save conversation transcript to data/")
    print("  /load <filename>          Load conversation transcript from data/")
    print("  /exit                     Exit BlazeAI\n")


def handle_settings_command(args: list[str]):
    """Views or modifies sampling parameters."""
    if not args:
        print("\n[Generation Settings]")
        print(f"  temperature        : {generation_config.temperature}")
        print(f"  top_p              : {generation_config.top_p}")
        print(f"  top_k              : {generation_config.top_k}")
        print(f"  max_new_tokens     : {generation_config.max_new_tokens}")
        print(f"  repetition_penalty : {generation_config.repetition_penalty}")
        print(f"  do_sample          : {generation_config.do_sample}")
        print("\nTo update, type: /settings <param> <value>\n")
        return

    if len(args) < 2:
        print("Usage: /settings <parameter> <value>")
        return

    param, val = args[0].lower(), args[1]
    try:
        if param == "temperature":
            generation_config.temperature = float(val)
        elif param == "top_p":
            generation_config.top_p = float(val)
        elif param == "top_k":
            generation_config.top_k = int(val)
        elif param == "max_new_tokens":
            generation_config.max_new_tokens = int(val)
        elif param == "repetition_penalty":
            generation_config.repetition_penalty = float(val)
        elif param == "do_sample":
            generation_config.do_sample = val.lower() in ("true", "1", "yes")
        else:
            print(f"Unknown parameter: {param}")
            return
        print(f"[Settings] Updated {param} to {val}")
    except ValueError as e:
        print(f"[Settings Error] Invalid value: {e}")


def handle_model_command(args: list[str], model_manager: ModelManager):
    """Shows or switches the active model."""
    if not args:
        info = model_manager.get_model_info()
        print("\n[Active Model Information]")
        for k, v in info.items():
            print(f"  {k:<14} : {v}")
        print("\nAvailable preset models:")
        for m in system_config.available_models:
            marker = " (Active)" if m == model_manager.model_id else ""
            print(f"  - {m}{marker}")
        print("\nTo switch, type: /model <model_id>\n")
        return

    new_model_id = args[0]
    print(f"\n[Model] Switching model to '{new_model_id}'...")
    try:
        model_manager.load_model(new_model_id)
        print(f"[Model] Successfully loaded '{new_model_id}' in {model_manager.load_time_sec:.2f}s\n")
    except Exception as e:
        print(f"[Model Error] Failed to load model: {e}\n")


def main():
    print(BANNER)
    
    # Initialize components
    model_mgr = ModelManager.get_instance()
    conv_mgr = ConversationManager()
    engine = InferenceEngine()

    print(f"Initializing local language model: {system_config.default_model_id}")
    print("Loading weights into RAM (this happens once)...")
    
    try:
        model_mgr.load_model()
        print(f"Model ready in {model_mgr.load_time_sec:.2f}s! Inference device: CPU ({system_config.cpu_threads} threads).")
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Please check your internet connection or model cache.")
        sys.exit(1)

    print("Type your message to chat, or type /help for commands.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting BlazeAI. Goodbye!")
            break

        if not user_input:
            continue

        # Command handling
        if user_input.startswith("/"):
            parts = user_input.split()
            cmd = parts[0].lower()
            args = parts[1:]

            if cmd in ("/exit", "/quit"):
                print("Exiting BlazeAI. Goodbye!")
                break
            elif cmd == "/help":
                print_help()
            elif cmd == "/clear":
                conv_mgr.clear()
                print("[Conversation history cleared]\n")
            elif cmd == "/model":
                handle_model_command(args, model_mgr)
            elif cmd == "/stats":
                print("\n" + session_benchmark.format_stats_report() + "\n")
            elif cmd == "/settings":
                handle_settings_command(args)
            elif cmd == "/save":
                filename = args[0] if args else None
                try:
                    saved_path = conv_mgr.save(filename)
                    print(f"[Saved] Conversation transcript saved to: {saved_path.name}\n")
                except Exception as e:
                    print(f"[Save Error] {e}\n")
            elif cmd == "/load":
                if not args:
                    print("Usage: /load <filename>\n")
                else:
                    try:
                        turns = conv_mgr.load(args[0])
                        print(f"[Loaded] Successfully restored {turns} turns.\n")
                    except Exception as e:
                        print(f"[Load Error] {e}\n")
            else:
                print(f"Unknown command '{cmd}'. Type /help for available commands.\n")
            continue

        # Real Model Generation Loop
        print("\nBlazeAI: ", end="", flush=True)

        def stream_callback(token_text: str):
            sys.stdout.write(token_text)
            sys.stdout.flush()

        try:
            full_response, metrics = engine.stream_generate(
                conversation_manager=conv_mgr,
                user_input=user_input,
                on_token_callback=stream_callback
            )
            print("\n")
            print(metrics.summary_line())
            print()
        except KeyboardInterrupt:
            print("\n[Generation interrupted by user]\n")
        except Exception as e:
            print(f"\n[Inference Error] {e}\n")


if __name__ == "__main__":
    main()
