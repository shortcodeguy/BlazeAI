"""
BlazeAI v5 - Verification Test Suite
Tests model loading, streaming inference, context management, and benchmarks.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import generation_config, system_config
from conversation import ConversationManager
from model import ModelManager
from inference import InferenceEngine
from benchmark import session_benchmark, get_current_ram_mb


def test_blazeai():
    print("========================================")
    print("  BlazeAI v5 - Automated Verification   ")
    print("========================================")

    # 1. Model Loading
    print("\n[Test 1] Testing Model Initialization...")
    model_mgr = ModelManager.get_instance()
    model, tokenizer = model_mgr.load_model()
    assert model is not None, "Model failed to load!"
    assert tokenizer is not None, "Tokenizer failed to load!"
    info = model_mgr.get_model_info()
    print(f"Model: {info['model_id']} | Parameters: {info['parameters']} | Load Time: {info['load_time']}")

    # 2. Conversation & Prompt Handling
    print("\n[Test 2] Testing Conversation & Memory...")
    conv_mgr = ConversationManager()
    engine = InferenceEngine()

    # Reduce max_new_tokens for quick test verification
    generation_config.max_new_tokens = 50

    # 3. Test with a novel, unanticipated question
    test_question_1 = "Why do leaves change color in autumn?"
    print(f"\n[Test 3] Inferencing Question 1: '{test_question_1}'")
    streamed_tokens = []

    def callback(t: str):
        streamed_tokens.append(t)
        sys.stdout.write(t)
        sys.stdout.flush()

    print("Response: ", end="")
    resp1, metrics1 = engine.stream_generate(conv_mgr, test_question_1, callback)
    print("\n" + metrics1.summary_line())

    assert len(resp1) > 0, "Response should not be empty!"
    assert len(streamed_tokens) > 0, "Tokens should have streamed!"
    assert metrics1.generated_tokens > 0, "Generated token count must be > 0"
    assert metrics1.time_to_first_token_sec > 0, "TTFT must be > 0"
    assert metrics1.tokens_per_sec > 0, "Tokens/sec must be > 0"

    # 4. Multi-turn context test
    test_question_2 = "Can you summarize that in 5 words?"
    print(f"\n[Test 4] Multi-turn Follow-up: '{test_question_2}'")
    print("Response: ", end="")
    resp2, metrics2 = engine.stream_generate(conv_mgr, test_question_2, callback)
    print("\n" + metrics2.summary_line())

    assert len(conv_mgr.history) == 4, f"Expected 4 history turns (2 user, 2 assistant), got {len(conv_mgr.history)}"

    # 5. Test Save & Load
    print("\n[Test 5] Testing Conversation Save & Load...")
    saved_path = conv_mgr.save("test_run.json")
    assert saved_path.exists(), f"File {saved_path} was not created!"
    print(f"Transcript saved to {saved_path.name}")

    fresh_conv = ConversationManager()
    loaded_count = fresh_conv.load("test_run.json")
    assert loaded_count == 4, f"Expected 4 loaded turns, got {loaded_count}"
    print(f"Successfully loaded {loaded_count} turns into fresh conversation manager.")

    # 6. Session Benchmark Report
    print("\n[Test 6] Testing Benchmark Report...")
    stats = session_benchmark.format_stats_report()
    print(stats)
    assert session_benchmark.total_turns == 2, "Expected 2 turns recorded in benchmark"

    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! BlazeAI v5 is fully operational. <<<")


if __name__ == "__main__":
    test_blazeai()
