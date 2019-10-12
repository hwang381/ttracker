# [DEPRECATED] ttracker
An automatically triggered time-tracker for all major desktop OS'es and browsers

## Run and develop from source

### Prerequisites
* `Python 3`
* [`virtualenv`](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/)

#### Prepare on Linux
```bash
python3 -m virtualenv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements_linux.txt
```

#### Prepare on macOS
```bash
python3 -m virtualenv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements_macos.txt
```

#### Prepare on Windows (assume using Powershell and [`Set-ExecutionPolicy`](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.security/set-executionpolicy?view=powershell-6) is set to `Unrestricted`)
```powershell
python3 -m virtualenv venv
.\venv\Scripts\activate.ps1
pip install -r requirements.txt -r requirements_win.txt
```

#### Start on Linux or macOS
```bash
source venv/bin/activate
python start.py
# optionally, use `LOGGING=debug python start.py` to get more verbose logging
```

#### Start on Windows
```powershell
.\venv\Scripts\activate.ps1
# optionally, use `$env:LOGGING = "debug"` to get more verbose logging
python start.py
```

Visit [localhost:16789](http://localhost:16789) to view the web interface

## (Recommended) More precise time tracking within browsers
Nowadays a lot of applications camouflage themselves as web applications

This application however only tracks "traditional desktop applications", e.g. if you spend 30 minutes on `gmail.com` and 30 minutes on `your-company.slack.com`, all you will get is 1 hour time spent within your browser, and yet it's important for you to know that you actually spent 30 minutes on Email and 30 minutes on Slack

Check out the following browser extensions so that you will get more precise time tracking based on the sites that you visit within the browser
* [Firefox](https://github.com/hwang381/ttracker-ff-ext)
