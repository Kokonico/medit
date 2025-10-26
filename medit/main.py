"""medit: a non-interactive text editor for terminal."""
import sys
import os
import argparse

from objlog import LogNode, LogMessage
from objlog.LogMessages import Debug, Info, Warn, Error, Fatal


class Line(LogMessage):
    # blank color
    color = "\033[0m"
    level = "Medit"

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

LOG = LogNode("medit", print_filter=[Line, Fatal, Info], print_to_console=True, log_file=LOG_DIR)

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
        for i, line in enumerate(content.splitlines()):
            # if not the last line, print a newline
            line_obj = Line(line)
            # set level to line number
            line_obj.level = i+1
            print(line_obj.colored())

def main():
    parser = argparse.ArgumentParser(description="medit: a non-interactive text editor for terminal.")
    parser.add_argument("file", help="The file to edit.")
    parser.add_argument("--version", action="version", version=f"medit {VERSION}")
    args = parser.parse_args()
    
    begin_editing(args.file)