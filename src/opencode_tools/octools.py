import os
import re
import json
import glob as glob_module
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path


def read_tool(filepath: str, offset: int = 1, limit: int = 2000) -> str:
    """
    Read a file or list a directory.

    - For files: returns content with line number prefixes.
    - For directories: returns entries, subdirectories have trailing /.

    Args:
        filepath: Absolute path to file or directory.
        offset:   Starting line (1-indexed). Default 1.
        limit:    Max lines to return. Default 2000.

    Returns:
        Formatted content string.
    """

    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {filepath}")

    # --- Directory listing ---
    if path.is_dir():
        entries = sorted(path.iterdir(), key=lambda p: (
            not p.is_dir(), p.name.lower()))
        result = []
        for entry in entries:
            suffix = "/" if entry.is_dir() else ""
            result.append(f"{entry.name}{suffix}")
        return "\n".join(result) if result else "(empty directory)"

    # --- File reading ---
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    total = len(lines)
    start = max(0, offset - 1)
    end = min(start + limit, total)

    if start >= total:
        return f"(offset {offset} is beyond file length {total})"

    result = []
    for i in range(start, end):
        line = lines[i].rstrip("\n").rstrip("\r")
        if len(line) > 2000:
            line = line[:2000] + "... [truncated]"
        result.append(f"{i + 1}: {line}")

    output = "\n".join(result)
    if end < total:
        output += f"\n... ({total - end} more lines)"

    return output


def write_tool(filepath: str, content: str) -> str:
    """
    Write content to a file. Overwrites if exists, creates dirs if needed.

    Args:
        filepath: Absolute path to write to.
        content:  Text content to write.

    Returns:
        Confirmation message.
    """

    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} bytes to {filepath}"


def edit_tool(filepath: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
    """
    Replace exact text in a file (string replacement, not regex).

    Args:
        filepath:    Absolute path to the file.
        old_string:  Text to find (must match exactly, including whitespace).
        new_string:  Text to replace with.
        replace_all: If True, replace ALL occurrences. If False, replace first.

    Returns:
        Description of what was changed.
    """

    path = Path(filepath)
    if not path.exists():
        return f"Error: file does not exist: {filepath}"

    original = path.read_text(encoding="utf-8")

    if old_string not in original:
        # Try to show what's nearby to help debug
        lines = original.splitlines()
        first_word = old_string.split()[:2]
        nearby = [l for l in lines if any(w in l for w in first_word)]
        hint = ""
        if nearby:
            hint = f"\nDid you mean one of these lines?\n" + \
                "\n".join(nearby[:5])
        return f"Error: old_string not found in file.{hint}"

    if not replace_all and original.count(old_string) > 1:
        return ("Error: Found multiple matches. Either use replace_all=True "
                "or provide more surrounding context in old_string.")

    if replace_all:
        new_content = original.replace(old_string, new_string)
        count = original.count(old_string)
    else:
        new_content = original.replace(old_string, new_string, 1)
        count = 1

    path.write_text(new_content, encoding="utf-8")
    return f"Replaced {count} occurrence(s) in {filepath}"


def glob_tool(pattern: str, path: str = ".") -> str:
    """
    Find files matching a glob pattern.

    Examples:
        **/*.py         -> all Python files recursively
        src/**/*.ts     -> TypeScript files under src/
        *.md            -> markdown files in current dir only

    Args:
        pattern: Glob pattern to match.
        path:    Root directory to search in. Default current dir.

    Returns:
        Matching file paths, one per line.
    """

    root = Path(path)
    if not root.exists():
        return f"Error: directory not found: {path}"

    matches = []
    for p in root.rglob(pattern):
        if p.is_file():
            matches.append(
                str(p.relative_to(root) if root != Path(".") else p))

    matches.sort()
    return "\n".join(matches) if matches else "No files found."


def grep_tool(pattern: str, path: str = ".", include: str = None) -> str:
    """
    Search file contents using a regular expression.

    Args:
        pattern: Regex pattern to search for.
        path:    Root directory to search.
        include: Optional glob filter (e.g., "*.py", "*.{ts,js}").

    Returns:
        Lines formatted as "filepath:line_number: content".
    """

    root = Path(path)
    if not root.exists():
        return f"Error: directory not found: {path}"

    try:
        regex = re.compile(pattern)
    except re.error as e:
        return f"Invalid regex: {e}"

    # Collect files
    if include:
        files = [p for p in root.rglob(include) if p.is_file()]
    else:
        files = [p for p in root.rglob("*") if p.is_file()]

    # Skip binary extensions
    binary = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip",
              ".tar", ".gz", ".exe", ".dll", ".so", ".dylib", ".pyc", ".o", ".a", ".lib", ".pyd", ".whl"}

    matches = []
    MAX_MATCHES = 200

    for fp in files:
        if fp.suffix.lower() in binary:
            continue
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    if regex.search(line):
                        rel = fp.relative_to(root)
                        matches.append(f"{rel}: {i}: {line.rstrip()}")
                        if len(matches) >= MAX_MATCHES:
                            break
        except Exception:
            continue
        if len(matches) >= MAX_MATCHES:
            break

    if not matches:
        return "No matches found."
    result = "\n".join(matches)
    if len(matches) >= MAX_MATCHES:
        result += f"\n... (hit limit of {MAX_MATCHES})"
    return result


def bash_tool(command: str, timeout: int = 120000, workdir: str = None) -> str:
    """
    Execute a shell command and return its output.

    Args:
        command: Shell command to run.
        timeout: Max time in milliseconds. Default 120000 (2 min).
        workdir: Working directory for the command. Default None (current).

    Returns:
        Combined stdout and stderr as a string.
    """

    timeout_sec = timeout / 1000

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            cwd=workdir
        )
        output = ""
        if result.stdout:
            output += result.stdout
            if not output.endswith("\n"):
                output += "\n"
        if result.stderr:
            output += f"[stderr]\n{result.stderr}"
            if not output.endswith("\n"):
                output += "\n"

        if result.returncode != 0:
            output += f"\n(exit code: {result.returncode})"

        # Truncate very long output
        MAX_OUTPUT = 50000
        if len(output) > MAX_OUTPUT:
            output = output[:MAX_OUTPUT] + \
                f"\n... (output truncated at {MAX_OUTPUT} chars)"

        return output if output else "(no output)"

    except subprocess.TimeoutExpired:
        return f"(command timed out after {timeout}ms)"
    except Exception as e:
        return f"(error executing command: {e})"


def webfetch_tool(url: str, format: str = "markdown") -> str:
    """
    Fetch content from a URL.

    Args:
        url:    Fully qualified URL (http/https).
        format: Output format: "markdown", "text", or "html". Default "markdown".

    Returns:
        Page content in requested format.
    """

    # Upgrade http to https:
    if url.startswith("http://"):
        url = "https://" + url[7:]

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/120.0.0.0 Safari/537.36")
            }
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"Error fetching URL: {e}"

    if format == "html":
        return html

    if format == "text":
        # Simple HTML-to-text conversion
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        # Truncate at 10000 chars
        MAX_LEN = 10000
        if len(text) > MAX_LEN:
            text = text[:MAX_LEN] + f"\n... (truncated at {MAX_LEN} chars)"
        return text

    # "markdown" - basic conversion
    text = html
    # Remove scripts and styles
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", text, flags=re.DOTALL)
    # Convert headings
    for i in range(6, 0, -1):
        text = re.sub(rf"<h{i}[^>]*>(.*?)</h{i}>",
                      f"{'#' * i} \\1", text, flags=re.DOTALL)
    # Convert links
    text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                  r"[\2](\1)", text, flags=re.DOTALL)
    # Convert bold/italic
    text = re.sub(r"<(b|strong)[^>]*>(.*?)</\1>",
                  r"**\2**", text, flags=re.DOTALL)
    text = re.sub(r"<(i|em)[^>]*>(.*?)</\1>", r"*\2*", text, flags=re.DOTALL)
    # Convert code
    text = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", text, flags=re.DOTALL)
    text = re.sub(r"<pre[^>]*>(.*?)</pre>",
                  r"```\n\1\n```", text, flags=re.DOTALL)
    # Convert paragraphs
    text = re.sub(r"<p[^>]*>(.*?)</p>", r"\n\n\1\n\n", text, flags=re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text)
    # Convert lists
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"- \1", text, flags=re.DOTALL)
    # Remove remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Collapse whitespace
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    MAX_LEN = 10000
    if len(text) > MAX_LEN:
        text = text[:MAX_LEN] + f"\n... (truncated at {MAX_LEN} chars)"

    return text


def websearch_tool(query: str, num_results: int = 8) -> str:
    """
    Search the web and return results.

    This uses a basic approach. In production you'd use a real search API.
    By default this version just returns a message explaining search would
    be done via the configured search provider.

    Args:
        query:       Search query string.
        num_results: Number of results to return (default 8).

    Returns:
        Search results as formatted text.
    """

    # In the real agent, this connects to a search provider.
    # Here's a minimal implementation using DuckDuckGo's lite version.
    try:
        url = "https://lite.duckduckgo.com/lite/"
        data = urllib.parse.urlencode({"q": query}).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={"User-Agent": "Mozilla/5.0",
                     "Content-Type": "application/x-www-form-urlencoded"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"Search failed: {e}"

    # Extract result links from DuckDuckGo lite
    results = []
    # Find all <a> tags with class "result-link" or similar
    for m in re.finditer(r'<a[^>]*href="([^"]*)"[^>]*class="[^"]*result-link[^"]*"[^>]*>(.*?)</a>', html, re.DOTALL):
        url = m.group(1)
        title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        results.append(f"{title}\n {url}")
        if len(results) >= num_results:
            break

    # Fallback: try basic result extraction
    if not results:
        for m in re.finditer(r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL):
            url = m.group(1)
            title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if title and "duckduckgo" not in url.lower():
                results.append(f"{title}\n {url}")
                if len(results) >= num_results:
                    break

    if results:
        return f"Search results for '{query}':\n\n" + "\n\n".join(results[:num_results])
    else:
        return (f"Could not extract results for '{query}'. In a real agent this would use the configured search provider.")


def question_tool(question: str, options: list, header: str = "", multiple: bool = False) -> str:
    """
    Ask the user a question with predefined options.

    Displays the question and options, waits for user selection.
    Returns the selected option(s).

    Args:
        question: The question text.
        options:  List of option strings, or list of dicts with
                  {"label": "...", "description": "..."}.
        header:   Short header (max 30 chars).
        multiple: Allow selecting multiple options.
    Returns:
    """
    print(f"\n{'=' * 60}")
    if header:
        print(f"[{header}]")
    print(f"Question: {question}")
    print()

    normalized = []
    for opt in options:
        if isinstance(opt, dict):
            normalized.append((opt["label"], opt.get("description", "")))
        else:
            normalized.append((str(opt), ""))

    for i, (label, desc) in enumerate(normalized, 1):
        line = f"  {i}. {label}"
        if desc:
            line += f"  ({desc})"
        print(line)

    if multiple:
        print("\n(Enter numbers separated by commas, e.g. '1,3')")
    else:
        print("\n(Enter a number)")

    choice = input("\nYour choice: ").strip()

    if multiple:
        indices = [int(x.strip())
                   for x in choice.split(",") if x.strip().isdigit()]
        selected = [normalized[i - 1][0]
                    for i in indices if 0 < i <= len(normalized)]
        return ", ".join(selected) if selected else "(no valid selection)"
    else:
        try:
            idx = int(choice)
            if 1 <= idx <= len(normalized):
                return normalized[idx - 1][0]
        except ValueError:
            pass
        return f"(custom response: {choice})"


def task_tool(description: str, prompt: str, subagent_type: str = "general") -> str:
    """
    Launch a sub-agent to handle a task autonomously.

    In the real system, this spawns a separate agent with its own tools.
    In this reference implementation, it prints the task details and
    returns a placeholder - you'd connect this to your actual agent system.

    Args:
        description:   Short task description (3-5 words).
        prompt:        Full instructions for the sub-agent.
        subagent_type: Agent type: "explore" (fast research) or
                       "general" (multistep tasks). Default "general".
     Returns:
        Result from the sub-agent.
    """

    payload = {
        "tool": "task",
        "subagent_type": subagent_type,
        "description": description,
        "prompt": prompt,
    }
    # In the real implementation, this spawns an agent.
    # For this reference file, we return the serialized task so your
    # agent framework can handle it.
    return json.dumps(payload, indent=2)


def todowrite_tool(todos: list, description: str = "") -> str:
    """
    Create or update a structured task list.

    Each todo is a dict: {"content": "...", "status": "...", "priority": "..."}
    Status: "pending", "in_progress", "completed", "cancelled"
    Priority: "high", "medium", "low"

    Only ONE task can be "in_progress" at a time.

    Args:
        todos:       List of task dicts.
        description: Optional description of what this todo list tracks.

    Returns:
        Formatted task list as a string.
    """

    status_icons = {
        "pending": "🟠",
        "in_progress": "🔵",
        "completed": "🟢",
        "cancelled": "❌",
    }

    priority_colors = {
        "high": "HIGH",
        "medium": "MED",
        "low": "LOW",
    }

    lines = []
    if description:
        lines.append(f"Task list: {description}")
        lines.append("")

    for t in todos:
        content = t.get("content", "?")
        status = t.get("status", "pending")
        priority = t.get("priority", "medium")
        icon = status_icons.get(status, "🟠")
        prio = priority_colors.get(priority, "MED")
        lines.append(f" [{icon}] {content} ({prio}, {status})")

    # Count summary
    counts = {}
    for t in todos:
        s = t.get("status", "pending")
        counts[s] = counts.get(s, 0) + 1
    summary = ", ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
    lines.append(f"\nSummary: {summary}")

    return "\n".join(lines)


def skill_tool(name: str) -> str:
    """
    Load a specialized skill with instructions and resources.

    Skills provide curated workflows for specific tasks.

    Args:
        name: Name of the skill to load (from available_skills list).

    Returns:
        Skills instructions as a string, or error if not found.
    """

    available = {
        "customize-opencode": "Configuration skill for opencode settings, agents, MCP servers, etc.",
    }
    if name in available:
        return f"Loaded skill: {name}\nDescription: {available[name]}"
    return f"Skill '{name}' not found. Available: {', '.join(available.keys())}"


def list_tools():
    """List all available tools with their signatures."""
    tools = {
        "read_tool":      "(filepath, offset=1, limit=20000)",
        "write_tool":     "(filepath, content)",
        "edit_tool":      "(filepath, old_string, new_string, replace_all=False)",
        "glob_tool":      "(pattern, path='.')",
        "grep_tool":      "(pattern, path='.', include=None)",
        "bash_tool":      "(command, timeout=120000, workdir=None)",
        "webfetch_tool":  "(url, format='markdown')",
        "websearch_tool": "(query, num_results=8)",
        "question_tool":  "(question, options, header='', multiple=False)",
        "task_tool":      "(description, prompt, subagent_type='general')",
        "todowrite_tool": "(todos, description='')",
        "skill_tool":     "(name)",
    }
    result = []
    for name, sig in tools.items():
        result.append(f"{name}{sig}")
    return "\n".join(result)


if __name__ == "__main__":
    print("=" * 60)
    print("AGENT TOOLS REFERENCE IMPLEMENTATION")
    print("=" * 60)
    print()
    print(list_tools())
    print()
    print("Example - read_tool on this file (first 5 lines):")
    print(read_tool(__file__, offset=1, limit=5))
