from objlog import LogMessage

class Line(LogMessage):
    # blank color
    color = "\033[0m"
    level = "Medit"

class File:
    """Represents a file being edited."""
    def __init__(self, path, content: list[Line]):
        self.path = path
        self.content = content

    def refresh_lines(self):
        """Refresh the line numbers."""
        for i, line in enumerate(self.content):
            newline = Line(line.message)
            newline.level = f"{i+1}"
            self.content[i] = newline

    def save(self):
        """Save the file to disk."""
        with open(self.path, 'w') as f:
            for line in self.content:
                f.write(line.message + '\n')

    def unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        try:
            with open(self.path, 'r') as f:
                disk_content = f.read().splitlines()
        except FileNotFoundError:
            disk_content = []

        in_memory_content = [line.message for line in self.content]
        return disk_content != in_memory_content
