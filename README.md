# ttracker
An application-triggered time-tracker for all major desktop OS'es

## Run from source

### Prerequisites
* `Python 3`
* `pip`
(The following assumes `Python 3` is installed as `python3` and `pip` as `pip3`. Change commands to `python` and `pip` if you see appropriate)

### Ubuntu (or any OS with X11, hopefully)

```bash
pip3 install -r requirements.txt -r requirements_x11.txt
python3 server.py
```

Visit [localhost:16789](http://localhost:16789) to view the web interface

## (Recommended) More precise time tracking within browsers
Nowadays a lot of applications camouflage themselves as web applications
This application however only tracks "traditional desktop applications", e.g. if you spend 30 minutes on `gmail.com` and 30 minutes on `your-company.slack.com`
All you will get is 1 hour time spent within your browser, and yet it's important for you to know that you actually spent 30 minutes on Email and 30 minutes on Slack

Check out the following browser extensions so that you will get more precise time tracking based on the sites that you visit within the browser
* [for Firefox](https://github.com/hwang381/ttracker-ff-ext)
