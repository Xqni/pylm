import ast
import os
import glob


def read_file(filepath: str) -> str:
    """Read the contents of a specific text file."""
    if not os.path.exists(filepath) or not os.path.isfile(filepath):
        return f"Error: {filepath} likely doesn't exist or is a directory not a file. Use list_files() to see its contents of the folder first."
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(string_to_write: str, filepath: str) -> str:
    """Write content of a specific text file."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            return f.write(string_to_write)
    except Exception as e:
        return f"Error writing file: {e}"


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


def read_specific_lines(filepath: str, start: int, end: int) -> list:
    """Read the specific lines of a text file."""
    if not os.path.exists(filepath):
        return f"Error: {filepath} doesn't exist. Check whether you are passing in the current filepath. Use list_files() to the list of files in the directory."
    elif not os.path.isfile(filepath):
        return f"Error: {filepath} is not a file. It may be a directory, use list_files() to see its contents."
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.readlines()
            return content[start:end]
    except Exception as e:
        return f"Error reading file: {e}"


def glob_files(pattern: str, path: str = '.') -> str:
    """
    Find files by glob pattern (**/*.py, *.json, etc.)
    This function returns a list of matches, use the results as needed for answers.
    """
    try:
        if matches := glob.glob(f'{pattern}', recursive=True):
            return matches
        else:
            return f"No matches were found for the {pattern}. Use a different pattern to search for files or use different tool."
    except Exception as e:
        return f"Error finding the {pattern}: {e}"


def change_cwd(path: str) -> str:
    """
    Change the current working directory.
    """
    try:
        os.chdir(path)
        return f"Current working directory is now: {get_cwd()}"
    except Exception as e:
        os.chdir(get_cwd())
        return f"Error changing directory to {path}. Error message: {e}. Restoring the path. Current working directory is now: {get_cwd()}"


def create_dir(directory_name: str) -> str:
    """
    Create an empty directory with the specified name.
    To create nested directories, call the function multiple times with updated directory name.
    You may want to use change_cwd() tool to change into the newly created directory to create nested directories, otherwise it is not required.
    """
    try:
        os.mkdir(directory_name)
        return f"Directory '{directory_name}' created successfully."
    except FileExistsError:
        return f"Directory '{directory_name}' already exists."
    except PermissionError:
        return f"Permission denied: Unable to create '{directory_name}'."
    except Exception as e:
        return f"An error occurred: {e}"
