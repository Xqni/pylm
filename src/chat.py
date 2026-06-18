from ollama import chat
from .config import (
  OLLAMA_MODEL
)

class LlamaChat:
  def get_response(self, messages):
    stream = chat(
        model=OLLAMA_MODEL,
        messages=messages,
        think=True,
        stream=True,
    )

    thinking_phase = False
    response_started = False

    for chunk in stream:
        if chunk.message.thinking:
            if not thinking_phase:
                print(f"\033[2m[think] \033[0m", end="")
                thinking_phase = True
            print(f"\033[2m{chunk.message.thinking}\033[0m", end="", flush=True)
        if chunk.message.content:
            if not response_started:
                if thinking_phase:
                    print()
                print("Llama: ", end="")
                response_started = True
            print(chunk.message.content, end="", flush=True)
    print()
    