from ollama import chat
from .config import (
    OLLAMA_MODEL
)

from .tools import read_files, list_files


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
        self.messages.extend(messages)

        print("\033[2m[Qwen thinking...] \033[0m", end="\r")

        # Agent Loop
        while True:
            stream = chat(
                model=self.model,
                messages=self.messages,
                tools=self.tool_list,
                think=True,
                stream=True,
            )

            full_content = ""
            tool_calls = None
            started = False
            for chunk in stream:
                if chunk.message.thinking:
                    print(f"\033[2m{chunk.message.thinking}\033[0m", end="", flush=True)
                if chunk.message.content:
                    if not started:
                        print("\nQwen: ", end="")
                        started = True
                    print(chunk.message.content, end="", flush=True)
                    full_content += chunk.message.content
                if chunk.done and chunk.done_reason == "tool_calls":
                    tool_calls = chunk.message.tool_calls

        # model used a tool
            if tool_calls:
                # Add the model's tool request to history so it remembers
                self.messages.append(stream.message)

                for tool in tool_calls:
                    tool_name = tool.function.name
                    arguments = tool.function.arguments

                    print(
                        f"\033[2mQwen: [calling {tool_name} with {arguments}]\033[0m", end="\n")

                    function_to_call = self.available_tools.get(tool_name)
                    if function_to_call:
                        result = function_to_call(**arguments)

                        self.messages.append({
                            "role": "tool",
                            "content": str(result),
                            "tool_name": tool_name
                        })

                # The loop auto restarts here!
                # It sends the new history (with the tool results) back to the model.

            # the model did not call a tool
            else:
                self.messages.append({
                    "role": "assistant",
                    "content": full_content
                })
                break
        print()