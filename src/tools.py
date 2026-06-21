import os
import ast


def read_file(filepath: str) -> str:
    """Read the contents of a specific text file."""
    if not os.path.exists(filepath) or not os.path.isfile(filepath):
        return f"Error: {filepath} likely doesn't exist or is a directory not a file. Use list_files() to see its contents of the folder first."
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


def get_cwd() -> str:
    """Get the current working directory path."""
    return os.getcwd()


def python_code_parser(source_code: str) -> str:
    """
    Returns a string representation of the parsed AST. Useful for understanding code structure.
    """
    try:
        parsed_ast = ast.parse(source_code)
        return ast.dump(parsed_ast)
    except Exception as e:
        return f"Error parsing source code: {e}. Use read_file() tool to read its content instead."
