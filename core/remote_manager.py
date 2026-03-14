import subprocess


class RemoteManager:

    def __init__(self, conn):

        self.host = conn["host"]
        self.user = conn["user"]
        self.key = conn["key"]

    def run(self, command):

        ssh_cmd = ["ssh"]

        if self.key:
            ssh_cmd += ["-i", self.key]

        ssh_cmd += [f"{self.user}@{self.host}", command]

        result = subprocess.run(
            ssh_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        return result.stdout
