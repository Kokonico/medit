"""medit: a non-interactive text editor for terminal."""
import sys
import os
import argparse

from objlog import LogNode, LogMessage
from objlog.LogMessages import Debug, Info, Warn, Error, Fatal

from .classes import Line, File

# get os log directory for different os's

match sys.platform:
    case "linux" | "linux2":
        LOG_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "medit", "medit.log")
    case "darwin":
        LOG_DIR = os.path.join(os.path.expanduser("~"), "Library", "Logs", "medit", "medit.log")
    case "win32":
        LOG_DIR = os.path.join(os.getenv("APPDATA"), "medit", "medit.log")
    case _:
        LOG_DIR = os.path.join(os.path.expanduser("~"), "medit.log")

# Ensure the log directory exists
# this variable will exist, ignore warning
os.makedirs(os.path.dirname(LOG_DIR), exist_ok=True)

LOG = LogNode("medit", print_filter=[Fatal, Info], print_to_console=True, log_file=LOG_DIR)

VERSION = "1.0.0"

def begin_editing(file_path):
    """Begin editing the specified file."""
    if not os.path.exists(file_path):
        LOG.log(Debug(f"File {file_path} does not exist. Creating a new file."))
        with open(file_path, 'w') as f:
            pass  # Create an empty file
    else:
        LOG.log(Info(f"Opening file {file_path} for editing."))
    # Here would be the logic to open the file in a text editor mode
    LOG.log(Info(f"Editing file: {file_path}"))
    # now, print each line with the Line.colored() method
    with open(file_path, 'r+') as f:
        content = f.read()
        # create the File object
        lines = [Line(line) for line in content.splitlines()]
        # set level for each line to be the line number
        for i, line in enumerate(lines):
            line.level = f"{i+1}"
        file = File(file_path, lines)
        # we got the data, now edit it
    edit(file)

def edit(file: File):
    """Edit the file in a non-interactive way."""
    # so, we need to have all the lines before the cursor printed
    # then the line with the cursor should have the content on that line
    # be easily editable (input only lets you add new content)
    cursor_position = len(file.content) - 1 # start at the end of the file
    # calculate context lines to show based on terminal size
    context_size = max(5, (os.get_terminal_size().lines - 3) // 2)
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        file.refresh_lines()
        for line in file.show_lines_near(cursor_position, context=context_size):
            if int(line.level) - 1 == cursor_position:
                print(f"\u001b[32m> {line}\u001b[0m")  # green color for current line
            else:
                print(f"  {line}")
        command = input("::> ").lower().strip()

        parts = command.split()
        LOG.log(Debug(f"Command parts: {parts}"))

        match parts[0]:
            case "q" | "quit":
                LOG.log(Info("Exiting editor."))
                break
            case "u" | "up":
                if cursor_position > 0:
                    # check if a second argument is given, if so, move up as many lines as specified (unless out of bounds, clamp it)
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
                            cursor_position = min(len(file.content) - 1, cursor_position + amount)
                    except (IndexError, ValueError):
                        cursor_position += 1
            case "a" | "add":
                # check if args were given, if so, add that line instead of prompting
                if len(parts) > 1:
                    new_line = " ".join(parts[1:])
                else:
                    new_line = input("New line content: ")
                file.content.insert(cursor_position + 1, Line(new_line))
                cursor_position += 1
            case "e" | "edit":
                # same as add, check for args
                if len(parts) > 1:
                    new_content = " ".join(parts[1:])
                else:
                    new_content = input(f"E ({file.content[cursor_position].content}) / ")
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
                print("  n, newline     - Add a new line after the cursor (same as add, but without prompt)")
                print("  h, help       - Show this help message")
                input("Press Enter to continue...")

            case _:
                LOG.log(Warn(f"Unknown command: {command}"))
    # check for unsaved changes before exiting
    if file.unsaved_changes():
        save = input("You have unsaved changes. Save before exiting? (y/n): ").lower().strip()
        if save == 'y':
            file.save()
            LOG.log(Info(f"File {file.path} saved."))

def main():
    parser = argparse.ArgumentParser(description="medit: a non-interactive text editor for terminal.")
    parser.add_argument("file", nargs='?', help="The file to edit.")
    parser.add_argument("--version", action="version", version=f"medit {VERSION}")
    args = parser.parse_args()

    # If no file argument is provided, create an in-memory empty File and edit it.
    if args.file is None:
        file = File(None, [])
        edit(file)
    else:
        begin_editing(args.file)