"""
BlazeAI v5 - Conversation State & History Management
Created by ShortCodeGuy Studio

Manages live multi-turn conversational state, context window boundary trimming,
and transcript persistence (save/load). Contains ZERO hardcoded knowledge or answers.
"""

import json
import time
from pathlib import Path
from typing import Any, Optional
from config import DATA_DIR, system_config
from prompts import DEFAULT_SYSTEM_PROMPT, build_chat_messages


class ConversationManager:
    """Manages conversational turns, bounded memory, and JSON serialization."""
    
    def __init__(self, system_prompt: str = DEFAULT_SYSTEM_PROMPT):
        self.system_prompt = system_prompt
        self.history: list[dict[str, str]] = []

    def add_user_message(self, content: str):
        """Append user turn to history."""
        self.history.append({"role": "user", "content": content})

    def add_assistant_message(self, content: str):
        """Append assistant turn to history."""
        self.history.append({"role": "assistant", "content": content})

    def clear(self):
        """Reset conversation turns."""
        self.history.clear()

    def get_messages(self, current_user_input: str) -> list[dict[str, str]]:
        """Construct full chat message structure for the model."""
        return build_chat_messages(
            history=self.history,
            user_input=current_user_input,
            system_prompt=self.system_prompt
        )

    def trim_context(self, tokenizer: Any, max_tokens: int = system_config.max_context_tokens) -> int:
        """
        Trims older turns from conversation history if token length exceeds max_tokens.
        Preserves most recent context and leaves room for model generation.
        Returns the number of turns removed.
        """
        removed_turns = 0
        if not self.history:
            return 0

        while len(self.history) > 2:
            # Format candidate messages
            formatted = build_chat_messages(self.history, "", self.system_prompt)
            try:
                tokens = tokenizer.apply_chat_template(
                    formatted,
                    tokenize=True,
                    add_generation_prompt=True,
                    return_tensors=None
                )
                if len(tokens) <= max_tokens:
                    break
            except Exception:
                # If apply_chat_template fails without input, check raw character length fallback
                if len(self.history) <= system_config.history_turns_limit:
                    break

            # Remove oldest turn pair (user + assistant) to maintain dialogue symmetry
            if len(self.history) >= 2:
                self.history.pop(0)
                self.history.pop(0)
                removed_turns += 2
            else:
                self.history.pop(0)
                removed_turns += 1

        return removed_turns

    def save(self, filename: Optional[str] = None) -> Path:
        """Saves current conversation transcript to the data/ directory as JSON."""
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"
        
        if not filename.endswith(".json"):
            filename += ".json"
            
        target_path = DATA_DIR / filename
        data = {
            "title": "BlazeAI Conversation Transcript",
            "creator": "ShortCodeGuy Studio",
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_prompt": self.system_prompt,
            "turns_count": len(self.history),
            "history": self.history
        }
        
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        return target_path

    def load(self, filename: str) -> int:
        """Loads conversation transcript from the data/ directory."""
        if not filename.endswith(".json"):
            filename += ".json"
            
        target_path = DATA_DIR / filename
        if not target_path.exists():
            # Try checking absolute path
            target_path = Path(filename)
            if not target_path.exists():
                raise FileNotFoundError(f"Transcript file not found: {filename}")
                
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        if "history" not in data or not isinstance(data["history"], list):
            raise ValueError("Invalid transcript format: missing 'history' list.")
            
        self.history = data["history"]
        if "system_prompt" in data:
            self.system_prompt = data["system_prompt"]
            
        return len(self.history)
