import multiprocessing
from flask import Flask, request
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


flask_app.run(host='127.0.0.1', port=16789)
