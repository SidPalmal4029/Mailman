from core.utils import run_command


class AsperaTool:
    name = "ascp"
    def transfer(self, src, dst, conn, bandwidth=None, direction="push"):
        cmd = ["ascp"]
        if conn["key"]:
            cmd += ["-i", conn["key"]]
        if bandwidth:
            cmd += ["-l", str(bandwidth)]
        if direction == "push":
            source = src
            dest = f"{conn['user']}@{conn['host']}:{dst}"
        else:
            source = f"{conn['user']}@{conn['host']}:{src}"
            dest = dst
        cmd += [source, dest]
        run_command(cmd)
