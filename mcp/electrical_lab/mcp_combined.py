"""Local compatibility entry point for the two archived v3 teaching toolkits.

The original packages stay intact. Shared tools use current; five unique
modeling tools are retained from the earlier archive. No network or hardware I/O.
"""
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.stdin.reconfigure(encoding="utf-8")
sys.stdout.reconfigure(encoding="utf-8")


def load_server(name, folder):
    sys.path.insert(0, str(ROOT / folder))
    spec = importlib.util.spec_from_file_location(name, ROOT / folder / "mcp_server.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


current = load_server("training_current", "current")
earlier = load_server("training_modeling", "modeling")
current_execute = current.execute
current_names = {tool["name"] for tool in current.TOOLS}
extra_tools = [tool for tool in earlier.TOOLS if tool["name"] not in current_names]
extra_names = {tool["name"] for tool in extra_tools}
current.TOOLS = current.TOOLS + extra_tools

# Independent two-route teaching model; keep archived fluorescent models intact.
two_route_spec = importlib.util.spec_from_file_location("two_route_extension", ROOT / "two_route" / "mcp_extension.py")
two_route = importlib.util.module_from_spec(two_route_spec)
two_route_spec.loader.exec_module(two_route)
two_route_names = {tool["name"] for tool in two_route.TOOLS}
current.TOOLS = current.TOOLS + two_route.TOOLS


def execute(name, args):
    if name in two_route_names:
        return two_route.execute(name, args)
    if name in extra_names:
        return earlier.execute(name, args)
    return current_execute(name, args)


current.execute = execute

if __name__ == "__main__":
    current.main()
