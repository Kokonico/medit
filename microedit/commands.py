"""Commands module"""

from .classes import File, Line, EditCommandResult
from .constants import LOG, VERSION

from objlog.LogMessages import Debug, Info, Warn, Error

# command decorator, registers commands and their logic
command_registry = {}


def command(shortname, name):
    """Decorator to register a command."""

    def decorator(func):
        command_registry[shortname] = func
        command_registry[name] = func
        return func

    return decorator


@command("h", "help")
def help_command(file, cursor_position, *args):
    """Show help information."""
    print("Commands:")
    print("  q, quit       - Exit the editor")
    print("  u, up         - Move cursor up")
    print("  g, goto       - Go to a specific line number")
    print("  d, down       - Move cursor down")
    print("  a, add        - Add a new line after the cursor")
    print("  e, edit       - Edit the current line")
    print(
        "  i, insert     - Insert text onto the current line (append, doesn't replace)"
    )
    print("  r, remove   - Delete the current line")
    print("  s, save       - Save the file")
    print(
        "  n, newline     - Add a new line after the cursor (same as add, but without prompt)"
    )
    print("  h, help       - Show this help message")
    input("Press Enter to continue...")
    return EditCommandResult(
        quit_editor=False,
        cursor_position=cursor_position,
        file=file,
        feedback=Info("Displayed help information."),
    )


@command("q", "quit")
def quit_command(file, cursor_position, *args):
    """Quit the editor."""
    return EditCommandResult(
        quit_editor=True,
        cursor_position=cursor_position,
        file=file,
        feedback=Info("Editor exited."),
    )


@command("u", "up")
def up_command(file, cursor_position, *args):
    """Move the cursor up by X lines."""
    lines_to_move = 1
    try:
        lines_to_move = int(args[0])
    except (IndexError, ValueError):
        pass
    if lines_to_move == -1:
        new_position = 0
    else:
        new_position = max(0, cursor_position - lines_to_move)
    return EditCommandResult(
        quit_editor=False,
        cursor_position=new_position,
        file=file,
        feedback=Info(
            f"Cursor has not moved."
            if new_position == cursor_position
            else f"Cursor now at line {new_position + 1}."
        ),
    )


@command("g", "goto")
def goto_command(file, cursor_position, *args):
    """Go to a specific line number."""
    try:
        line_number = int(args[0]) - 1  # convert to 0-indexed
        if 0 <= line_number < len(file.content):
            return EditCommandResult(
                quit_editor=False,
                cursor_position=line_number,
                file=file,
                feedback=Info(f"Cursor moved to line {line_number + 1}."),
            )
        else:
            result = Warn(f"Line number {line_number + 1} is out of range.")
    except (IndexError, ValueError) as e:
        if isinstance(e, IndexError):
            result = Warn("No line number provided for goto command.")
        else:
            result = Warn("Invalid line number for goto command.")
    return EditCommandResult(
        quit_editor=False, cursor_position=cursor_position, file=file, feedback=result
    )


@command("d", "down")
def down_command(file, cursor_position, *args):
    """Move the cursor down by X lines."""
    lines_to_move = 1
    try:
        if args[0] == "-1":
            # move to last line
            return EditCommandResult(
                quit_editor=False,
                cursor_position=len(file.content) - 1,
                file=file,
                feedback=Info(
                    "Cursor has not moved."
                    if cursor_position == len(file.content) - 1
                    else f"Cursor now at line {len(file.content)}."
                ),
            )
        lines_to_move = int(args[0])
    except (IndexError, ValueError):
        pass
    new_position = max(0, min(len(file.content) - 1, cursor_position + lines_to_move))
    return EditCommandResult(
        quit_editor=False,
        cursor_position=new_position,
        file=file,
        feedback=Info(
            "Cursor has not moved."
            if new_position == cursor_position
            else f"Cursor now at line {new_position + 1}."
        ),
    )


@command("a", "add")
def add_command(file, cursor_position, *args):
    """Add a new line after the cursor."""
    if args:
        new_line = " ".join(args)
    else:
        new_line = input("New line content: ")
    file.content.insert(cursor_position + 1, Line(new_line))
    new_cursor_position = (
        cursor_position + 1 if len(file.content) > 1 else cursor_position
    )
    return EditCommandResult(
        quit_editor=False,
        cursor_position=new_cursor_position,
        file=file,
        feedback=Info("Line added."),
    )


@command("e", "edit")
def edit_command(file, cursor_position, *args):
    """Edit the current line."""
    if args:
        new_content = " ".join(args)
    else:
        current_text = (
            file.content[cursor_position].content
            if len(file.content) > 0 and cursor_position < len(file.content)
            else ""
        )
        new_content = input(f"E ({current_text}) / ")
    if len(file.content) > 0 and cursor_position < len(file.content):
        file.content[cursor_position].content = new_content
    elif len(file.content) == 0:
        file.content.append(Line(new_content))
        cursor_position = 0  # Set cursor to first line
    return EditCommandResult(
        quit_editor=False,
        cursor_position=cursor_position,
        file=file,
        feedback=Info("Line edited."),
    )


@command("i", "insert")
def insert_command(file, cursor_position, *args):
    """Insert text onto the current line (append, doesn't replace)."""

    if len(file.content) == 0 or cursor_position >= len(file.content):
        # If there are no lines, we need to add one first
        file.content.append(Line(""))
        cursor_position = 0

    if args:
        insert_text = " ".join(args)
    else:
        insert_text = input(f"I ({file.content[cursor_position].content}) / ")

    separator = " " if file.content[cursor_position].content != "" else ""
    file.content[cursor_position].content += separator + insert_text
    return EditCommandResult(
        quit_editor=False,
        cursor_position=cursor_position,
        file=file,
        feedback=Info("Text inserted."),
    )


@command("r", "remove")
def remove_command(file, cursor_position, *args):
    """Delete the current line."""
    if len(file.content) > 0 and cursor_position < len(file.content):
        file.content.pop(cursor_position)
        new_cursor_position = max(0, min(cursor_position, len(file.content) - 1))
        return EditCommandResult(
            quit_editor=False,
            cursor_position=new_cursor_position,
            file=file,
            feedback=Info("Line removed."),
        )
    else:
        return EditCommandResult(
            quit_editor=False,
            cursor_position=cursor_position,
            file=file,
            feedback=Warn("No line to remove at the current cursor position."),
        )


@command("s", "save")
def save_command(file, cursor_position, *args):
    """Save the file."""
    file.save()
    return EditCommandResult(
        quit_editor=False,
        cursor_position=cursor_position,
        file=file,
        feedback=Info(f"File {file.path} saved."),
    )


@command("n", "newline")
def newline_command(file, cursor_position, *args):
    """Add a new line after the cursor (same as add, but without prompt)."""
    file.content.insert(cursor_position + 1, Line(""))
    new_cursor_position = (
        max(0, cursor_position + 1) if len(file.content) > 1 else cursor_position
    )
    return EditCommandResult(
        quit_editor=False,
        cursor_position=new_cursor_position,
        file=file,
        feedback=Info("Newline added."),
    )


def execute_command(name, file, cursor_position, *args) -> EditCommandResult:
    """Execute a command by name."""
    if name in command_registry:
        return command_registry[name](file, cursor_position, *args)
    else:
        return EditCommandResult(
            quit_editor=False,
            cursor_position=cursor_position,
            file=file,
            feedback=Error(f"Unknown command: {name}"),
        )
