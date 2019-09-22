import multiprocessing
import logging
from flask import Flask, request, jsonify, send_from_directory
from urllib.parse import urlparse
from database.sqlite_store import SqliteStore
from desktop.tell_os import is_linux, is_macos

###
# Initialize storage
##
store = SqliteStore("db.sqlite")


###
# Setup desktop app monitoring
##
def desktop_monitor_callback(program_name: str):
    print(f"Desktop app focused to program {program_name}")


def start_desktop_monitor():
    if is_linux():
        from desktop.linux import LinuxDesktopMonitor
        desktop_monitor_constructor = LinuxDesktopMonitor
    elif is_macos():
        from desktop.macos import MacOSDesktopMonitor
        desktop_monitor_constructor = MacOSDesktopMonitor
    else:
        raise RuntimeError("Unsupported OS")
    desktop_monitor = desktop_monitor_constructor(desktop_monitor_callback)
    desktop_monitor.start()


desktop_monitor_p = multiprocessing.Process(target=start_desktop_monitor)
desktop_monitor_p.start()


###
# Start webapp
##
flask_app = Flask(__name__)
# Less verbose logging from Flask
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)


@flask_app.route('/')
def index():
    return send_from_directory('web', 'index.html')


flask_app.run(host='127.0.0.1', port=16789)
