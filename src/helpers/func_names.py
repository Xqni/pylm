import inspect
from ..opencode_tools import octools


def get_tool_registry():
    return {
        name: func for name, func in inspect.getmembers(octools, inspect.isfunction) if not name.startswith('_')
    }
