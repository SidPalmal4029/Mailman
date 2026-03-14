class BaseTool:

    name = "base"

    def available(self):
        raise NotImplementedError
    def send(self, src, dst, conn):
        raise NotImplementedError
    def fetch(self, src, dst, conn):
        raise NotImplementedError
    def sync(self, src, dst, conn):
        raise NotImplementedError
