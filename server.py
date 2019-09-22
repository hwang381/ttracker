import multiprocessing
import time
import logging
from flask import Flask, request, jsonify, send_from_directory
from urllib.parse import urlparse
from database.sqlite_store import SqliteStore
from desktop.tell_os import is_linux, is_macos
from database.time import now_milliseconds

###
# Initialize storage
##
store = SqliteStore("db.sqlite")


###
# Setup heartbeat
##
def start_heartbeat():
    last_heartbeat = store.get_heartbeat()
    if last_heartbeat != 0:
        store.append_event_with_timestamp(last_heartbeat, 'exit', '')
    while True:
        store.heartbeat()
        time.sleep(5)


heartbeat_p = multiprocessing.Process(target=start_heartbeat)
heartbeat_p.start()


###
# Setup desktop app monitoring
##
def desktop_app_monitoring_callback(program_name: str):
    print(f"Desktop app focused to program {program_name}")
    store.append_event("desktop_app_focus", program_name)


def start_desktop_app_monitoring():
    if is_linux():
        from desktop.linux import LinuxDesktopAppMonitor
        desktop_app_monitor_constructor = LinuxDesktopAppMonitor
    elif is_macos():
        from desktop.macos import MacOSDesktopAppMonitor
        desktop_app_monitor_constructor = MacOSDesktopAppMonitor
    else:
        raise RuntimeError("Unsupported window manager")
    desktop_app_monitor = desktop_app_monitor_constructor()
    desktop_app_monitor.set_callback(desktop_app_monitoring_callback)
    desktop_app_monitor.start()


desktop_app_monitor_p = multiprocessing.Process(target=start_desktop_app_monitoring)
desktop_app_monitor_p.start()


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


@flask_app.route('/api/ping', methods=['GET'])
def ping():
    return 'pong'


@flask_app.route('/api/event/browser_tab_focus', methods=['POST'])
def append_browser_tab_focus_event():
    url = request.data.decode('utf-8')
    print(f"Browser tab focused to url {url}")
    parse_result = urlparse(url)
    netloc = parse_result.netloc
    if netloc:
        store.append_event('browser_tab_focus', netloc)
    return 'browser_tab_focus event processed'


@flask_app.route('/api/stats', methods=['GET'])
def get_stats():
    from_timestamp = request.args.get('from')
    to_timestamp = request.args.get('to')
    if not from_timestamp or not to_timestamp:
        return 'from or to missing', 400
    if from_timestamp > to_timestamp:
        return 'from is bigger than to', 400
    from_timestamp = int(from_timestamp)
    to_timestamp = min(int(to_timestamp), now_milliseconds())
    events = store.get_events(from_timestamp, to_timestamp)
    stats = {}

    for i in range(len(events) - 1):
        event_timestamp, event_type, event_host = events[i]
        if event_type != 'exit':
            next_event_timestamp, _, _ = events[i + 1]
            stats[event_host] = stats.get(event_host, 0) + (next_event_timestamp - event_timestamp)

    last_event_timestamp, last_event_type, last_event_host = events[-1]
    if last_event_type != 'exit':
        stats[last_event_host] = stats.get(last_event_host, 0) + (to_timestamp - last_event_timestamp)

    return jsonify(stats)


flask_app.run(host='127.0.0.1', port=16789)
