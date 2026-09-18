"""
BlazeAI v5 - Prompts & Formatting
Created by ShortCodeGuy Studio

Defines behavioral and communication guidelines for the model.
Strictly contains NO domain facts, NO encyclopedic data, NO prewritten answers.
"""

from typing import Any

# Pure behavioral instructions - zero factual knowledge, zero prewritten Q&As
DEFAULT_SYSTEM_PROMPT = (
    "You are BlazeAI, an intelligent conversational AI assistant created by ShortCodeGuy Studio. "
    "Communicate in clear, natural English. "
    "Follow the user's instructions carefully, provide direct and accurate explanations, "
    "and maintain context across turns. "
    "Avoid unnecessary repetition. If you are uncertain about something, state it candidly. "
    "Provide well-reasoned, concise, and helpful answers."
)


def build_chat_messages(
    history: list[dict[str, str]],
    user_input: str,
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
) -> list[dict[str, str]]:
    """
    Constructs the standard messages array for the model chat template.
    Structure:
    [
        {"role": "system", "content": ...},
        {"role": "user", "content": ...},
        {"role": "assistant", "content": ...},
        ...
        {"role": "user", "content": <current_input>}
    ]
    """
    messages: list[dict[str, str]] = []
    
    # 1. System behavioral prompt
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
        
    # 2. Prior conversation history
    for turn in history:
        messages.append({"role": turn["role"], "content": turn["content"]})
        
    # 3. Current user message
    messages.append({"role": "user", "content": user_input})
    
    return messages
