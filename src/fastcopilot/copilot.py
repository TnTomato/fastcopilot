import asyncio
import functools
import json

import openai
from loguru import logger

from .exceptions import (
    AsyncFunctionNotSupported,
    DuplicateFuncSpec,
    InvalidFuncSpecSchema
)
from .schemas import FuncSpec


class Copilot:

    def __init__(
        self,
        *,
        system_prompt: str | None = None,
        api_key: str | None = None,
        model: str = "gpt-3.5-turbo-0613",
        temperature: float = 1.0,
        headers: dict | None = None,
        timeout: int | None = 30
    ):
        assert api_key is not None

        self.model = model
        self.temperature = temperature
        self.api_key = api_key
        self.headers = headers
        self.timeout = timeout

        self.messages = None  # type: list[dict] | None
        self.system_prompt = system_prompt
        if self.system_prompt:
            self.messages = [{
                "role": "system",
                "content": self.system_prompt
            }]
        self._functions = None  # type: list[dict] | None
        self._func_mapping = {}  # type: dict[str, FuncSpec]

    def register_functions(self, *specs: FuncSpec):
        """
        Add functions for OpenAI function_call.
        """
        if not self._functions:
            self._functions = []
        for spec in specs:
            func_name = spec.json_schema.get("name")
            if not func_name:
                raise InvalidFuncSpecSchema("`name` is required in json_schema")
            if self._func_mapping.get(spec.json_schema["name"]):
                raise DuplicateFuncSpec(f"Duplicate function name: `{func_name}`")
            self._func_mapping[func_name] = spec
            self._functions.append(spec.json_schema)

    @property
    def params(self) -> dict:
        p = {
            "api_key": self.api_key,
            "model": self.model,
            "messages": self.messages,
            "temperature": self.temperature,
            "timeout": self.timeout
        }
        if self._functions:
            p["functions"] = self._functions
        return p

    def run(self, ipt: str) -> tuple[str, dict]:
        """
        Get reply from copilot.
        """
        if not self.messages:
            self.messages = []

        self.messages.append(
            {
                "role": "user",
                "content": ipt.strip()
            }
        )
        response = openai.ChatCompletion.create(**self.params)
        resp_msg = response["choices"][0]["message"]
        while function_call := resp_msg.get("function_call"):
            func_name = function_call["name"]
            arguments = json.loads(function_call["arguments"])
            logger.debug(f"<FunctionCall>name: {func_name}, arguments: {arguments}")
            func_spec = self._func_mapping.get(func_name)
            if asyncio.iscoroutinefunction(func_spec.handler):
                raise AsyncFunctionNotSupported("Try `Copilot.arun()`")
            else:
                result = func_spec.handler(**arguments, headers=self.headers)

            self.messages.append(
                {
                    "role": "function",
                    "name": func_name,
                    "content": json.dumps(result, ensure_ascii=False)
                }
            )
            response = openai.ChatCompletion.create(**self.params)
            resp_msg = response["choices"][0]["message"]

        self.messages.append(
            {
                "role": "assistant",
                "content": response["choices"][0]["message"]["content"]
            }
        )

        usage = response["usage"]

        return response["choices"][0]["message"]["content"], usage

    async def arun(self, ipt: str) -> tuple[str, dict]:
        """
        Get reply asynchronously from copilot.
        """
        if not self.messages:
            self.messages = []

        self.messages.append(
            {
                "role": "user",
                "content": ipt.strip()
            }
        )
        response = await asyncio.to_thread(
            openai.ChatCompletion.create,
            **self.params
        )
        resp_msg = response["choices"][0]["message"]
        while function_call := resp_msg.get("function_call"):
            func_name = function_call["name"]
            arguments = json.loads(function_call["arguments"])
            logger.debug(f"<FunctionCall>name: {func_name}, arguments: {arguments}")
            func_spec = self._func_mapping.get(func_name)
            if asyncio.iscoroutinefunction(func_spec.handler):
                result = await func_spec.handler(**arguments,
                                                 headers=self.headers)
            else:
                result = await asyncio.to_thread(
                    func_spec.handler,
                    **arguments,
                    headers=self.headers
                )

            self.messages.append(
                {
                    "role": "function",
                    "name": func_name,
                    "content": json.dumps(result, ensure_ascii=False)
                }
            )
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                **self.params
            )
            resp_msg = response["choices"][0]["message"]

        self.messages.append(
            {
                "role": "assistant",
                "content": response["choices"][0]["message"]["content"]
            }
        )

        usage = response["usage"]

        return response["choices"][0]["message"]["content"], usage
