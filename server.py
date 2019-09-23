import multiprocessing
import logging
from urllib.parse import urlparse
from typing import Dict
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from database.sqlite_store import SqliteStore
from desktop.tell_os import is_linux, is_macos
from utils.time import now_milliseconds

###
# Initialize storage
##
store = SqliteStore("db.sqlite")


###
# Setup desktop monitoring
##
def start_desktop_monitor():
    if is_linux():
        from desktop.linux import LinuxDesktopMonitor
        desktop_monitor_constructor = LinuxDesktopMonitor
    elif is_macos():
        from desktop.macos import MacOSDesktopMonitor
        desktop_monitor_constructor = MacOSDesktopMonitor
    else:
        raise RuntimeError("Unsupported OS")
    desktop_monitor = desktop_monitor_constructor(store)
    desktop_monitor.start()


desktop_monitor_p = multiprocessing.Process(target=start_desktop_monitor)
desktop_monitor_p.start()


###
# Start webapp
##
flask_app = Flask(__name__)
CORS(flask_app)
# Less verbose logging from Flask
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.ERROR)


@flask_app.route('/')
def index():
    return send_from_directory('web', 'index.html')


@flask_app.route('/api/stats', methods=['GET'])
def api_stats():
    from_timestamp = request.args.get('from')
    to_timestamp = request.args.get('to')
    if not from_timestamp or not to_timestamp:
        return 'from or to missing', 400
    if from_timestamp > to_timestamp:
        return 'from is bigger than to', 400
    from_timestamp = int(from_timestamp)
    to_timestamp = min(int(to_timestamp), now_milliseconds())

    time_entries = store.get_time_entries(from_timestamp, to_timestamp)
    stats = {}  # type: Dict[str, int]
    for i in range(len(time_entries) - 1):
        time_entry = time_entries[i]
        to_timestamp = time_entry.to_timestamp if time_entry.to_timestamp != 0 else time_entries[i + 1].from_timestamp
        # todo: account for event_type as well
        stats[time_entry.origin] = stats.get(time_entry.origin, 0) + (to_timestamp - time_entry.from_timestamp)

    last_time_entry = time_entries[-1]
    last_to_timestamp = last_time_entry.to_timestamp if last_time_entry.to_timestamp != 0 else to_timestamp
    # todo: account for event_type as well
    stats[last_time_entry.origin] = stats.get(last_time_entry.origin, 0) \
                                    + (last_to_timestamp - last_time_entry.from_timestamp)

    return jsonify(stats)


@flask_app.route('/api/ping/browser', methods=['POST'])
def api_browser_ping():
    # todo: somehow verify the ping is actually coming from a verified extension
    url = request.data.decode('utf-8')
    parsed_url = urlparse(url)
    netloc = parsed_url.netloc
    if netloc:
        store.ping('browser', netloc)
        return 'browser ping successful'
    return 'no netloc'


flask_app.run(host='localhost', port=16789)
