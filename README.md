# llama-python

A CLI chatbot powered by [Ollama](https://ollama.ai) that gives an LLM agent autonomous access to tools — file system, web search, bash, and more.

Built with Qwen3:8b, but works with any Ollama-hosted model.

## Features

- **Tool-using agent** — the LLM can read/write/edit files, run shell commands, search the web, grep/glob code, and more
- **Streaming responses** — see the model's "thinking" and output in real time
- **Autonomous tool calls** — the model decides when and which tools to invoke, with results fed back into the conversation
- **REPL interface** — interactive chat loop with history
- **Configurable model** — swap models via a `.env` file

## Requirements

- Python >= 3.12
- [Ollama](https://ollama.ai) installed and running locally
- An Ollama model pulled (default: `qwen3:8b`)

## Installation

```bash
# Clone the repo
git clone <repo-url>
cd llama-python

# Install with pip
pip install .

# Or install with uv (recommended)
uv pip install -e .
```

## Configuration

Copy the environment template and set your model:

```bash
cp .env.example .env
```

The `.env` file supports:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_MODEL` | `qwen3:8b` | The Ollama model to use |

Pull your model if you haven't already:

```bash
ollama pull qwen3:8b
```

## Usage

```bash
# Via the installed command
start-chat

# Or directly
python -m src.main
```

Type your prompts at the `You:` prompt. The LLM will respond and may autonomously use tools to fulfill your request.

```
You: What files are in this project?

[model thinking...]
Model: Let me check the project structure.
[工具] read_tool(filepath=".")
[工具] glob_tool(pattern="**/*.py")

Model: Here's what I found: ...
```

Exit with `exit`, `quit`, `bye`, or Ctrl+C.

## Available Tools

The LLM has access to these tools via the `octools` module:

| Tool | Description |
|---|---|
| `read_tool` | Read files (with line numbers) or list directories |
| `write_tool` | Write or overwrite files |
| `edit_tool` | Find-and-replace text in files |
| `glob_tool` | Find files by glob pattern |
| `grep_tool` | Regex search across file contents |
| `bash_tool` | Execute shell commands |
| `webfetch_tool` | Fetch and convert web page content |
| `websearch_tool` | Search the web via DuckDuckGo |
| `question_tool` | Ask the user a multiple-choice question |
| `task_tool` | Spawn a sub-agent for autonomous tasks |
| `todowrite_tool` | Create/update a structured task list |
| `skill_tool` | Load a specialized skill |
| `list_tools` | List all available tools and their signatures |

## Project Structure

```
llmpy/
├── .env                    # Environment variables
├── .env.example            # Template for .env
├── pyproject.toml          # Project config & dependencies
├── uv.lock                 # Deterministic lockfile
└── src/
    ├── __init__.py
    ├── main.py             # CLI entry point (REPL)
    ├── chat.py             # Core LlamaChat agent loop
    ├── config.py           # Environment config loader
    ├── tools.py            # Legacy file tools (superseded)
    ├── helpers/
    │   ├── __init__.py
    │   └── func_names.py   # Tool registry (inspect-based)
    └── opencode_tools/
        ├── __init__.py
        └── octools.py      # Full agent tool suite
```

## Architecture

```
User Input (REPL)
      │
      ▼
  main()                    main.py
      │
      ▼
  LlamaChat.get_response()  chat.py
      │
      ├── Send messages + tools to Ollama (streaming)
      ├── Display assistant response
      ├── If tool calls:
      │     ├── call_tools() → func_names → octools.py
      │     └── Append results and LOOP
      └── If no tool calls:
            └── Return to user input
```

## License

MIT
