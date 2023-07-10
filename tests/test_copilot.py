import os

from src.fastcopilot.copilot import Copilot


api_key = os.getenv("OPENAI_API_KEY")


def test_copilot():
    copilot = Copilot(api_key=api_key)
    reply, _ = copilot.run("hi")
    assert isinstance(reply, str)
