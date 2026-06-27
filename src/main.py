from src.chat import LlamaChat


def main():
    print("Llama LLM Chat - Type 'exit' to quit.")

    chat = LlamaChat()
    messages = []

    while True:
        try:
            user_input = input("\nYou: ")

            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\nExiting. Goodbye!\n")
                break

            messages.append({"role": "user", "content": user_input})
            print()
            chat.get_response(messages)
        except KeyboardInterrupt:
            print("\n\nExiting. Goodbye!\n")
            break


if __name__ == "__main__":
    main()
