import os

import pytest

from src.fastcopilot.copilot import Copilot


pytest_plugins = ('pytest_asyncio',)

api_key = os.getenv("OPENAI_API_KEY")


def test_copilot():
    copilot = Copilot(api_key=api_key)
    reply, _ = copilot.run("hi")
    assert isinstance(reply, str)


@pytest.mark.asyncio
async def test_async_copilot():
    copilot = Copilot(api_key=api_key)
    reply, _ = await copilot.arun("hi")
    assert isinstance(reply, str)
