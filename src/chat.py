from ollama import chat
from .config import (
    OLLAMA_MODEL
)

from .tools import read_file, list_files, get_cwd, python_code_parser


class LlamaChat:
    def __init__(self, model=OLLAMA_MODEL) -> None:
        self.model = model
        self.messages = []

        self.available_tools = {
            "read_file": read_file,
            "list_files": list_files,
            "get_cwd": get_cwd,
            "python_code_parser": python_code_parser
        }

        self.tool_list = list(self.available_tools.values())

    def get_response(self, messages):
        # Initialize messages
        self.messages = messages

        # Initial print
        print("\033[2m[Qwen thinking...] \033[0m", end="\r")

        # Agent Loop
        while True:
            response = chat(
                model=self.model,
                messages=self.messages,
                tools=self.tool_list,
                stream=True,  # makes this a generator
            )

            # Accumulators
            content = ""
            thinking = ""
            tool_calls = []

            # Flags for printing
            content_started = False
            thinking_started = False

            # streaming the response in the terminal
            for chunk in response:
                if chunk.message.thinking:
                    if not thinking_started:
                        # Prefix for the thinking chunks, printed once
                        print("\033[2mQwen thinking: \033[0m", end="")
                        thinking_started = True
                    thinking += chunk.message.thinking
                    # Dimmed print for thinking
                    print(
                        f"\033[2m{chunk.message.thinking}\033[0m", end="", flush=True)
                if chunk.message.content:
                    if not content_started:
                        # Prefix for actual message chunks, only printed once
                        print("\nQwen: ", end="")
                        content_started = True
                    content += chunk.message.content
                    print(chunk.message.content, end="", flush=True)
                if chunk.message.tool_calls:
                    # Add tool calls to the tool_calls accumulator
                    tool_calls.extend(chunk.message.tool_calls)

            # Save the tool calls to the history after the 'for' loop ends
            self.messages.append({
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls
            })

            # Only if the agent called tools
            if tool_calls:
                self.call_tools(tool_calls)

                # Agent loops automatically here if the tool calling has not finished

            # Agent never called any tools or the tool calls have ended
            else:
                print()  # Newline before waiting for user input
                break

    def call_tools(self, tools_to_call):
        for tool in tools_to_call:
            # Extract the details
            tool_name = tool.function.name
            arguments = tool.function.arguments

            print(
                f"\n\033[2m[tool] {tool_name}({arguments})\033[0m\n")

            try:
                # If the function is in the available list of tools, call the function (or tool)
                if function_to_call := self.available_tools.get(tool_name):
                    result = function_to_call(**arguments)

                    # Add the result to the history for final response and tracking
                    self.messages.append({
                        "role": "tool",
                        "content": str(result),
                        "name": tool_name
                    })
                else:
                    tool_doesnt_exist = f"Error calling {tool_name} with {arguments}. Check the tool against available tools and call the correct tool with correct arguments."
                    self.messages.append({
                        "role": "tool",
                        "content": str(tool_doesnt_exist),
                        "name": tool_name
                    })
            except Exception as e:
                error_calling_tool = f"Error calling {tool_name} with {arguments}. Error message: {e}"
                self.messages.append({
                    "role": "tool",
                    "content": str(error_calling_tool),
                    "name": tool_name
                })
