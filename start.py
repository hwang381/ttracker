import multiprocessing
import logging
from typing import Dict
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from database.sqlite_store import SqliteStore
from database.ping import Ping
from desktop.tell_os import is_linux, is_macos
from utils.time import now_milliseconds
from utils.sanctioned_ping_types import SANCTIONED_PING_TYPES


###
# Setup logging
###
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(filename)s][%(levelname)s] %(message)s'
)
# less verbose logging from requests
logging.getLogger("requests").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
# Less verbose logging from Flask
logging.getLogger('werkzeug').setLevel(logging.ERROR)

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
    desktop_monitor = desktop_monitor_constructor()
    desktop_monitor.start()


desktop_monitor_p = multiprocessing.Process(target=start_desktop_monitor)
desktop_monitor_p.start()


###
# Start webapp
##
flask_app = Flask(__name__)
CORS(flask_app)


@flask_app.route('/')
def index():
    return send_from_directory('web', 'index.html')


@flask_app.route('/api/stats', methods=['GET'])
def api_stats():
    from_timestamp = request.args.get('from')
    to_timestamp = request.args.get('to')
    ping_type = request.args.get('type')

    if not from_timestamp or not to_timestamp or not ping_type:
        return 'from or to or type missing', 400
    if from_timestamp > to_timestamp:
        return 'from is bigger than to', 400
    if ping_type not in SANCTIONED_PING_TYPES:
        return 'type is invalid', 400

    from_timestamp = int(from_timestamp)
    to_timestamp = min(int(to_timestamp), now_milliseconds())

    stats = {}  # type: Dict[str, int]
    time_entries = store.get_time_entries(
        from_timestamp=from_timestamp,
        to_timestamp=to_timestamp,
        entry_type=ping_type
    )
    for time_entry in time_entries:
        origin = time_entry.origin
        duration = time_entry.to_timestamp - time_entry.from_timestamp
        if duration == 0:
            duration = 1
        stats[origin] = stats.get(origin, 0) + duration

    return jsonify(stats)


@flask_app.route('/api/ping/browser', methods=['POST'])
def api_browser_ping():
    # todo: somehow verify the ping is actually coming from a verified extension
    payload = request.json

    # check hostname
    if 'hostname' not in payload:
        return 'hostname not in payload', 400
    hostname = payload['hostname']

    logging.debug(f"Browser ping {hostname}")
    store.ping(Ping(
        timestamp=now_milliseconds(),
        ping_type='browser',
        origin=hostname,
    ))
    return 'browser ping successful'


@flask_app.route('/api/ping/desktop', methods=['POST'])
def api_desktop_ping():
    # todo: somehow verify the ping is actually coming from this application
    payload = request.json

    # check program
    if 'program' not in payload:
        return 'program not in payload', 400
    program = payload['program']

    logging.debug(f"Desktop ping {program}")
    store.ping(Ping(
        timestamp=now_milliseconds(),
        ping_type='desktop',
        origin=program
    ))
    return 'desktop ping successful'


flask_app.run(host='localhost', port=16789)
