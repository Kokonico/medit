"""Constants for medit"""
import sys
import os
from objlog.LogMessages import Fatal, Info
from objlog import LogNode

VERSION = "1.1.0"

LOG_DIR: str

match sys.platform:
    case "linux" | "linux2":
        LOG_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "medit", "medit.log")
    case "darwin":
        LOG_DIR = os.path.join(os.path.expanduser("~"), "Library", "Logs", "medit", "medit.log")
    case "win32":
        LOG_DIR = os.path.join(os.getenv("APPDATA"), "medit", "medit.log")
    case _:
        LOG_DIR = os.path.join(os.path.expanduser("~"), "medit.log")

LOG = LogNode("medit", print_filter=[Fatal, Info], print_to_console=True, log_file=LOG_DIR)
