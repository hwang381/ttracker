import multiprocessing
from flask import Flask, request, jsonify
from urllib.parse import urlparse
from desktop.x11 import X11DesktopAppChangeSource
from database.sqlite_store import SqliteStore


store = SqliteStore("db.sqlite")


def desktop_app_change_callback(program_name: str):
    print(f"Desktop app focused to program {program_name}")
    store.append_event("desktop_app_focus", program_name)


def start_desktop_app_change():
    desktop_app_change_source = X11DesktopAppChangeSource(desktop_app_change_callback)
    desktop_app_change_source.start()


desktop_app_change_p = multiprocessing.Process(target=start_desktop_app_change)
desktop_app_change_p.start()


flask_app = Flask(__name__)


@flask_app.route('/ping', methods=['GET'])
def ping():
    return 'pong'


@flask_app.route('/event/browser_tab_focus', methods=['POST'])
def append_browser_tab_focus_event():
    url = request.data
    print(f"Browser tab focused to url {url}")
    parse_result = urlparse(url)
    netloc = parse_result.netloc
    if netloc:
        store.append_event('browser_tab_focus', netloc)
    return '/event/browser_tab_focus'


@flask_app.route('/stats', methods=['GET'])
def get_stats():
    from_timestamp = request.args.get('from')
    to_timestamp = request.args.get('to')
    if not from_timestamp or not to_timestamp:
        return 'from or to missing', 400
    if from_timestamp > to_timestamp:
        return 'from is bigger than to', 400
    events = store.get_events(from_timestamp, to_timestamp)
    stats = {}
    for i in range(len(events) - 1):
        event_timestamp, _, event_host = events[i]
        next_event_timestamp, _, _ = events[i + 1]
        stats[event_host] = stats.get(event_host, 0) + (next_event_timestamp - event_timestamp)
    return jsonify(stats)


flask_app.run(host='127.0.0.1', port=16789)
