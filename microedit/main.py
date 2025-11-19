"""medit: a non-interactive text editor for terminal."""

import argparse
import os

from objlog.LogMessages import Debug, Info, Warn, Error

from .classes import Line, File, EditCommandResult
from .constants import LOG_DIR, LOG, VERSION, COMMAND_SEPARATOR_CHAR

from .commands import execute_command


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
    cursor_position = max(
        0, len(file.content) - 1
    )  # start at the end of the file, or 0 if empty
    # calculate context lines to show based on terminal size
    context_size = max(5, (os.get_terminal_size().lines - 3) // 2)
    status = Info("Entered edit mode. Type 'h' or 'help' for commands.")
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        file.refresh_lines()
        print(status.color + status.message + "\u001b[0m")
        for line in file.show_lines_near(cursor_position, context=context_size):
            if int(line.level) - 1 == cursor_position:
                print(f"\u001b[32m> {line}\u001b[0m")  # green color for current line
            else:
                print(f"  {line}")

        command = input("::> ").strip()

        result = run_commands(command, file, cursor_position)
        status = result.feedback if result.feedback else status
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

    last_feedback = None

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

        result = execute_command(parts[0], file, cursor_position, *parts[1:])
        file = result.file
        cursor_position = result.cursor_position
        if result.feedback:
            LOG.log(result.feedback)
            last_feedback = result.feedback
        if result.quit_editor:
            LOG.log(Info("Quit command received. Exiting editor."))
            return EditCommandResult(
                quit_editor=True,
                cursor_position=cursor_position,
                file=file,
                feedback=result.feedback,
            )

        LOG.log(Debug(f"Post-execution cursor position: {cursor_position}"))
    return EditCommandResult(
        quit_editor=False,
        cursor_position=cursor_position,
        file=file,
        feedback=last_feedback,
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
