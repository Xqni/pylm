import inspect
from .. import tools


def get_tool_registry():
    return {
        name: func for name, func in inspect.getmembers(tools, inspect.isfunction) if not name.startswith('_')
    }
