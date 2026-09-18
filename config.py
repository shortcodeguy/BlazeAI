"""
BlazeAI v5 - Configuration
Created by ShortCodeGuy Studio

Hardware-optimized configuration for CPU inference, memory limits,
generation parameters, and application paths.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"

# Ensure runtime directories exist
MODELS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class GenerationConfig:
    """Configurable sampling and generation hyperparameters."""
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    max_new_tokens: int = 512
    repetition_penalty: float = 1.1
    do_sample: bool = True


@dataclass
class SystemConfig:
    """Hardware and model runtime configuration."""
    # Default model: Qwen2.5-0.5B-Instruct is highly efficient on CPU & 8GB RAM
    default_model_id: str = "Qwen/Qwen2.5-0.5B-Instruct"
    
    # Alternative popular local models
    available_models: list[str] = field(default_factory=lambda: [
        "Qwen/Qwen2.5-0.5B-Instruct",
        "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
    ])
    
    # CPU thread tuning: default to physical/available cores
    cpu_threads: int = max(1, (os.cpu_count() or 4) - 1)
    
    # Memory and context bounds
    max_context_tokens: int = 2048
    history_turns_limit: int = 12
    
    # Device setup
    device: str = "cpu"
    dtype: str = "bfloat16"


# Global application configuration instances
generation_config = GenerationConfig()
system_config = SystemConfig()
