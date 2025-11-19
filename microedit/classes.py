import os.path

from objlog import LogMessage


class EditCommandResult:
    """Represents the result of an edit command."""

    def __init__(
        self,
        quit_editor: bool = False,
        cursor_position: int = 0,
        file: "File" = None,
        feedback: LogMessage = None,
    ):
        self.quit_editor = quit_editor
        self.cursor_position = cursor_position
        self.file = file
        self.feedback = feedback


class Line:
    level = "Medit"
    content = ""

    def __init__(self, content: str):
        self.content = content

    def __repr__(self):
        return f"|{self.level}| {self.content}"


class File:
    """Represents a file being edited."""

    def __init__(self, path, content: list[Line]):
        self.path = path
        self.content = content

    def show_lines_near(self, cursor_line: int, context: int = 5) -> list[Line]:
        """Show lines near the cursor line."""
        # also assume cursor_line is 0-indexed
        start = max(0, cursor_line - context)
        end = min(len(self.content), cursor_line + context + 1)
        # note: if one of the bounds is hit, we can try to extend the other side
        if start == 0:
            end = min(len(self.content), end + (context - cursor_line))
        elif end == len(self.content):
            start = max(0, start - (cursor_line + context - len(self.content) + 1))

        return self.content[start:end]

    def refresh_lines(self):
        """Refresh the line numbers."""

        # first, find the largest line number
        # (in terms of digits, ex: biggest is 1000, so 4 digits)
        digits = len(str(len(self.content)))

        for i, line in enumerate(self.content):
            newline = Line(line.content)
            # calculate level with leading zeros
            newline.level = f"{i+1}".rjust(digits, "0")
            self.content[i] = newline

    def save(self):
        """Save the file to disk."""

        # check if path is defined, if not, we'll ask for it
        if not self.path:
            self.path = os.path.join(
                os.path.curdir, input(f"Enter file path to save: {os.path.curdir}/")
            )

        with open(self.path, "w") as f:
            for line in self.content:
                f.write(line.content + "\n")

    def unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        if not self.path:
            # check if file is empty (also ignore whitespace/newlines)
            real_content = "".join([line.content.strip() for line in self.content])
            return bool(real_content)
        try:
            with open(self.path, "r") as f:
                disk_content = f.read().splitlines()
        except FileNotFoundError:
            disk_content = []

        in_memory_content = [line.content for line in self.content]
        return disk_content != in_memory_content

    def __len__(self):
        return len(self.content)
