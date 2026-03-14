from core.utils import run_command


class RcloneTool:

    name = "rclone"

    def transfer(self, src, dst, conn, bandwidth=None, direction="push"):

        remote = f"{conn['user']}@{conn['host']}:{dst}"

        if direction == "push":

            cmd = [
                "rclone",
                "copy",
                src,
                remote
            ]

        else:

            cmd = [
                "rclone",
                "copy",
                f"{conn['user']}@{conn['host']}:{src}",
                dst
            ]

        run_command(cmd)
