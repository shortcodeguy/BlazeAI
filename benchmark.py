"""
BlazeAI v5 - Benchmarking & Performance Metrics
Created by ShortCodeGuy Studio

Measures real-time performance including model load time, time-to-first-token (TTFT),
generation throughput (tokens/sec), prompt processing speed, and RAM usage.
Never fabricates metrics.
"""

import os
import time
from dataclasses import dataclass, field
from typing import Optional
import psutil


def get_current_ram_mb() -> float:
    """Returns the resident set size (RSS) RAM usage of the current process in MB."""
    try:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except Exception:
        return 0.0


def get_system_ram_info() -> dict[str, float]:
    """Returns system-wide RAM stats (used, total, percent)."""
    try:
        vm = psutil.virtual_memory()
        return {
            "total_mb": vm.total / (1024 * 1024),
            "used_mb": vm.used / (1024 * 1024),
            "free_mb": vm.free / (1024 * 1024),
            "percent": vm.percent,
        }
    except Exception:
        return {"total_mb": 0.0, "used_mb": 0.0, "free_mb": 0.0, "percent": 0.0}


@dataclass
class TurnMetrics:
    """Detailed performance metrics for a single inference generation turn."""
    prompt_tokens: int = 0
    generated_tokens: int = 0
    total_tokens: int = 0
    time_to_first_token_sec: float = 0.0
    generation_time_sec: float = 0.0
    total_latency_sec: float = 0.0
    tokens_per_sec: float = 0.0
    prompt_tokens_per_sec: float = 0.0
    process_ram_mb: float = 0.0
    system_ram_percent: float = 0.0

    def summary_line(self) -> str:
        """Returns a concise single-line performance readout for the terminal."""
        return (
            f"[Metrics] {self.generated_tokens} tokens | "
            f"TTFT: {self.time_to_first_token_sec * 1000:.0f}ms | "
            f"Speed: {self.tokens_per_sec:.2f} tok/s | "
            f"Process RAM: {self.process_ram_mb:.0f} MB"
        )


@dataclass
class SessionBenchmark:
    """Aggregates metrics across the entire user session."""
    model_name: str = ""
    model_load_time_sec: float = 0.0
    turns: list[TurnMetrics] = field(default_factory=list)

    def record_turn(self, metrics: TurnMetrics):
        self.turns.append(metrics)

    @property
    def total_turns(self) -> int:
        return len(self.turns)

    @property
    def total_tokens_generated(self) -> int:
        return sum(t.generated_tokens for t in self.turns)

    @property
    def average_speed_tok_per_sec(self) -> float:
        valid_speeds = [t.tokens_per_sec for t in self.turns if t.tokens_per_sec > 0]
        if not valid_speeds:
            return 0.0
        return sum(valid_speeds) / len(valid_speeds)

    @property
    def average_ttft_ms(self) -> float:
        valid_ttft = [t.time_to_first_token_sec * 1000 for t in self.turns if t.time_to_first_token_sec > 0]
        if not valid_ttft:
            return 0.0
        return sum(valid_ttft) / len(valid_ttft)

    def format_stats_report(self) -> str:
        """Generates a comprehensive diagnostic report for the /stats command."""
        sys_ram = get_system_ram_info()
        proc_ram = get_current_ram_mb()
        
        lines = [
            "============================================================",
            "                 BlazeAI v5 Session Diagnostics              ",
            "============================================================",
            f"  Model Loaded         : {self.model_name}",
            f"  Model Load Time      : {self.model_load_time_sec:.2f} s",
            f"  Total Session Turns  : {self.total_turns}",
            f"  Total Tokens Produced: {self.total_tokens_generated}",
            f"  Avg Generation Speed : {self.average_speed_tok_per_sec:.2f} tokens/s",
            f"  Avg TTFT             : {self.average_ttft_ms:.1f} ms",
            "------------------------------------------------------------",
            "  Memory Utilization:",
            f"    Process RAM (RSS)  : {proc_ram:.1f} MB",
            f"    System RAM Used    : {sys_ram['used_mb']:.0f} / {sys_ram['total_mb']:.0f} MB ({sys_ram['percent']}%)",
            "============================================================"
        ]
        return "\n".join(lines)


# Global session benchmark tracker
session_benchmark = SessionBenchmark()
