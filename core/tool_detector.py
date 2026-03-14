import shutil


class ToolDetector:

    PRIORITY = ["ascp", "rclone", "rsync", "scp"]

    def detect(self):

        available = []

        for tool in self.PRIORITY:
            if shutil.which(tool):
                available.append(tool)

        if not available:
            raise RuntimeError("No transfer tools found on system")

        return available
