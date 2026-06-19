import os

def read_files(filepath: str) -> str:
    """Read the contents of a specific text file."""
    if not os.path.isfile(filepath):
        return f"Error: {filepath} is a directory likely, not a file. Use list_files() to see its contents."
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


def list_files(directory: str) -> str:
    """Lists all files in a given directory."""
    try:
        files = os.listdir(directory)
        return f"Files in {directory}: {', '.join(files)}"
    except Exception as e:
        return f"Error listing directory {e}"