from ollama import chat
from .config import (
    OLLAMA_MODEL
)

import json

from .tools import read_files, list_files, get_cwd


class LlamaChat:
    def __init__(self, model=OLLAMA_MODEL) -> None:
        self.model = model
        self.messages = []

        self.available_tools = {
            "read_files": read_files,
            "list_files": list_files
        }

        self.tool_list = [read_files, list_files]

    def get_response(self, messages):
        self.messages = messages

        print("\033[2m[Qwen thinking...] \033[0m", end="\r")

        # Agent Loop
        while True:
            response = chat(
                model=self.model,
                messages=self.messages,
                tools=self.tool_list,
                think=True,
            )

            if response.message.thinking:
                print(
                    f"\033[2m{response.message.thinking}\033[0m", end="\n")
            if response.message.tool_calls:
                self.messages.append(response.message)

                for tool in response.message.tool_calls:
                    tool_name = tool.function.name
                    arguments = tool.function.arguments

                    print(
                        f"\033[2m[System: AI is running tool {tool_name} with {arguments}] \033[0m", end="\r")

                    function_to_call = self.available_tools.get(tool_name)
                    if function_to_call:
                        result = function_to_call(**arguments)

                        self.messages.append({
                            "role": "tool",
                            "content": str(result),
                            "tool_name": tool_name
                        })

            else:
                print(f"Qwen: {response.message.content}")
                self.messages.append(response.message)
                break
