"""Simple command line runner for the financial advisor chatbot.

Before starting this script you should train a model with `rasa train`
and run the action server with `rasa run actions` in a separate shell.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from rasa.core.agent import Agent
from rasa.core.utils import EndpointConfig
from rasa.model import get_latest_model

MODELS_DIR = Path("models")


async def _load_agent() -> Agent:
    model_path: Optional[str] = get_latest_model(str(MODELS_DIR))
    if not model_path:
        raise RuntimeError(
            "No trained model found. Please run `rasa train` before starting the chat interface."
        )

    action_endpoint = EndpointConfig(url="http://localhost:5055/webhook")
    return await Agent.load(model_path, action_endpoint=action_endpoint)


async def chat() -> None:
    agent = await _load_agent()
    print("Financial Advisor Chatbot is ready! Type 'quit' or 'exit' to stop.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nSession ended. Take care of your finances!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit"}:
            print("Bot: Talk to you soon!")
            break

        responses = await agent.handle_text(user_input)
        if not responses:
            print("Bot: I'm thinking about that. Could you try asking in a different way?")
            continue

        for message in responses:
            text = message.get("text")
            if text:
                print(f"Bot: {text}")


if __name__ == "__main__":
    asyncio.run(chat())
