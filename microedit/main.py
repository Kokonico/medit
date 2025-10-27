"""medit: a non-interactive text editor for terminal."""

import argparse
import os
from math import remainder

from objlog.LogMessages import Debug, Info, Warn, Error

from .classes import Line, File, EditCommandResult
from .constants import LOG_DIR, LOG, VERSION, COMMAND_SEPARATOR_CHAR


def get_file(file_path: str) -> File:
    """Get a File object from the specified file path."""
    if not os.path.exists(file_path):
        LOG.log(Error(f"File {file_path} does not exist."))
        raise FileNotFoundError(f"File {file_path} does not exist.")

    with open(file_path, "r") as f:
        content = f.read()
        lines = [Line(line) for line in content.splitlines()]
        # set level for each line to be the line number
        for i, line in enumerate(lines):
            line.level = f"{i+1}"
        return File(file_path, lines)


def get_or_create_file(file_path: str) -> File:
    """Get a File object from the specified file path, or create a new one if it doesn't exist."""
    if not os.path.exists(file_path):
        LOG.log(Debug(f"File {file_path} does not exist. Creating a new file."))
        with open(file_path, "w") as f:
            pass  # Create an empty file
        return File(file_path, [])
    else:
        return get_file(file_path)


def begin_editing(file_path):
    """Begin editing the specified file."""
    LOG.log(Info(f"Opening file {file_path} for editing."))
    LOG.log(Info(f"Editing file: {file_path}"))
    file = get_or_create_file(file_path)
    edit(file)


def edit(file: File):
    """Edit the file in a non-interactive way."""
    cursor_position = len(file.content) - 1  # start at the end of the file
    # calculate context lines to show based on terminal size
    context_size = max(5, (os.get_terminal_size().lines - 3) // 2)
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        file.refresh_lines()
        for line in file.show_lines_near(cursor_position, context=context_size):
            if int(line.level) - 1 == cursor_position:
                print(f"\u001b[32m> {line}\u001b[0m")  # green color for current line
            else:
                print(f"  {line}")

        command = input("::> ").strip()

        result = run_commands(command, file, cursor_position)
        cursor_position = result.cursor_position
        file = result.file
        if result.quit_editor:
            break
    # check for unsaved changes before exiting
    if file.unsaved_changes():
        save = (
            input("You have unsaved changes. Save before exiting? (y/n): ")
            .lower()
            .strip()
        )
        if save == "y":
            file.save()
            LOG.log(Info(f"File {file.path} saved."))


def run_commands(
    commands: str, file: File, cursor_position: int = 0
) -> EditCommandResult:
    """Run a series of commands on the file."""
    for command in commands.split(COMMAND_SEPARATOR_CHAR):
        command = command.strip()
        # prune empty commands
        if len(command) == 0:
            continue

        LOG.log(Debug(f"Running command: {command}"))

        parts = command.split()
        LOG.log(Debug(f"Command parts: {parts}"))
        LOG.log(Debug(f"Pre-execution cursor position: {cursor_position}"))

        if len(parts) <= 0:
            continue

        match parts[0].lower():
            case "q" | "quit":
                LOG.log(Info("Exiting editor."))
                return EditCommandResult(
                    quit_editor=True, cursor_position=cursor_position, file=file
                )
            case "u" | "up":
                if cursor_position > 0:
                    try:
                        amount = int(parts[1])
                        if amount == -1:
                            cursor_position = 0
                        else:
                            cursor_position = max(0, cursor_position - amount)
                    except (IndexError, ValueError):
                        cursor_position -= 1
            case "d" | "down":
                if cursor_position < len(file.content) - 1:
                    try:
                        amount = int(parts[1])
                        if amount == -1:
                            cursor_position = len(file.content) - 1
                        else:
                            cursor_position = min(
                                len(file.content) - 1, cursor_position + amount
                            )
                    except (IndexError, ValueError):
                        cursor_position += 1
            case "a" | "add":
                if len(parts) > 1:
                    new_line = " ".join(parts[1:])
                else:
                    new_line = input("New line content: ")
                file.content.insert(cursor_position + 1, Line(new_line))
                cursor_position += (
                    1 if len(file.content) > 1 else 0
                )  # if it's the first line, don't move cursor
            case "e" | "edit":
                if len(parts) > 1:
                    new_content = " ".join(parts[1:])
                else:
                    new_content = input(
                        f"E ({file.content[cursor_position].content}) / "
                    )

                if len(file.content) == 0:
                    file.content.append(Line(new_content))
                else:
                    file.content[cursor_position].content = new_content
            case "r" | "remove":
                if len(file.content) > 0:
                    file.content.pop(cursor_position)
                    if cursor_position >= len(file.content):
                        cursor_position = len(file.content) - 1
            case "s" | "save":
                file.save()
                LOG.log(Info(f"File {file.path} saved."))
            case "n" | "newline":
                file.content.insert(cursor_position + 1, Line(""))
                cursor_position += 1

            case "h" | "help":
                print("Commands:")
                print("  q, quit       - Exit the editor")
                print("  u, up         - Move cursor up")
                print("  d, down       - Move cursor down")
                print("  a, add        - Add a new line after the cursor")
                print("  e, edit       - Edit the current line")
                print("  r, remove   - Delete the current line")
                print("  s, save       - Save the file")
                print(
                    "  n, newline     - Add a new line after the cursor (same as add, but without prompt)"
                )
                print("  h, help       - Show this help message")
                input("Press Enter to continue...")

            case _:
                LOG.log(Warn(f"Unknown command: {command}"))
        LOG.log(Debug(f"Post-execution cursor position: {cursor_position}"))
    return EditCommandResult(
        quit_editor=False, cursor_position=cursor_position, file=file
    )


def main():
    parser = argparse.ArgumentParser(
        description="medit: a non-interactive text editor for terminal."
    )
    parser.add_argument("--version", action="version", version=f"medit {VERSION}")
    parser.add_argument("file", nargs="?", help="The file to edit.")
    parser.add_argument(
        "-c",
        "--command",
        help=f"Command(s) to run on the file, separated by '{COMMAND_SEPARATOR_CHAR}'. NOTE: all arguments after -c are considered part of the command.",
        nargs=argparse.REMAINDER,
    )
    args = parser.parse_args()

    LOG.log(Debug(f"Arguments: {args}"))

    if args.command:
        command_str = " ".join(args.command).strip()
        LOG.log(Debug(f"Command string: {command_str}"))

        if args.file is None:
            file = File(None, [])
        else:
            file = get_or_create_file(args.file)

        result = run_commands(command_str, file)
        result.file.refresh_lines()

        if result.quit_editor:
            LOG.log(Info("Exiting editor after command execution."))
        else:
            LOG.log(Info("Command(s) executed. Current file content:"))
            for line in result.file.content:
                print(line)
        result.file.save()

    elif args.file is None:
        file = File(None, [])
        edit(file)
    else:
        begin_editing(args.file)
