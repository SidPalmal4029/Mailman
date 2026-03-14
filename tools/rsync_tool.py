from core.utils import run_command

class RsyncTool:
    """
    Transfer implementation using rsync
    """
    name = "rsync"
    def transfer(self, src, dst, conn, bandwidth=None, direction="push"):
        ssh_cmd = "ssh"
        if conn["key"]:
            ssh_cmd += f" -i {conn['key']}"
        cmd = [
            "rsync",
            "-av",
            "--progress",
            "--partial",
            "--append",
            "-e",
            ssh_cmd
        ]

        # Optional bandwidth limit
        if bandwidth:
            cmd += ["--bwlimit", str(bandwidth)]
        if direction == "push":
            source = src
            destination = f"{conn['user']}@{conn['host']}:{dst}"
        elif direction == "pull":
            source = f"{conn['user']}@{conn['host']}:{src}"
            destination = dst
        else:
            raise ValueError("direction must be push or pull")
        cmd += [source, destination]
        run_command(cmd)
