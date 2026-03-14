from core.utils import run_command

class ScpTool:
    name = "scp"
    def transfer(self, src, dst, conn, bandwidth=None, direction="push"):
        cmd = ["scp"]
        if conn["key"]:
            cmd += ["-i", conn["key"]]
        if direction == "push":
            source = src
            dest = f"{conn['user']}@{conn['host']}:{dst}"
        else:
            source = f"{conn['user']}@{conn['host']}:{src}"
            dest = dst
        cmd += [source, dest]

        run_command(cmd)
