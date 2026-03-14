from core.tool_registry import ToolRegistry


class TransferEngine:
    def __init__(self, conn):
        self.conn = conn
        self.registry = ToolRegistry()
    def send(self, src, dst):
        for tool in self.registry.available_tools():
            try:
                tool.send(src, dst, self.conn)
                print(f"Transfer completed using {tool.name}")
                return
            except Exception as e:
                print(f"{tool.name} failed: {e}")
        raise RuntimeError("All tools failed")

    def fetch(self, src, dst):
        for tool in self.registry.available_tools():
            try:
                tool.fetch(src, dst, self.conn)
                print(f"Transfer completed using {tool.name}")
                return
            except Exception as e:
                print(f"{tool.name} failed: {e}")
        raise RuntimeError("All tools failed")
