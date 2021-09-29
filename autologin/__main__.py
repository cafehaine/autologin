from datetime import timedelta
import random
from time import sleep
from typing import Dict

import requests

# Urls and contents used to check if we are blocked
PORTAL_DETECT_URLS: Dict[str, str] = {
    "http://detectportal.firefox.com/canonical.html": '<meta http-equiv="refresh" content="0;url=https://support.mozilla.org/kb/captive-portal"/>',
    "http://nmcheck.gnome.org/check_network_status.txt": "NetworkManager is online",
    "http://ping.archlinux.org/": "This domain is used for connectivity checking (captive portal detection).",
}

CHECK_PERIOD = timedelta(seconds=60)


class PortalHandler(ABC):
    def __init__(self, config) -> None:
        self._config = config

    @abstractmethod
    def login(self, url: str, portal: str) -> None:
        ...


class ULCOPortalHandler(PortalHandler):
    def login(self, url: str, portal: str) -> None:
        pass  # TODO actually do the requests to login


def get_portal_handler(url: str, portal: str) -> PortalHandler:
    """Return a PortalHandler based on the portal's contents."""
    # TODO detect portal, for now only support for ULCO's portal
    return ULCOPortalHandler


def login(config, url: str, portal: str) -> None:
    """Select a portal handler, and then call the login method."""
    portal_handler = get_portal_handler(portal)
    print(f"Detected portal of type {portal_handler.__class__.__name__}.")
    portal_handler(config).login(url, portal)


def check_online(config) -> None:
    """Check if the computer is online, and login if a portal is detected."""
    url, expected_content = random.choice(PORTAL_DETECT_URLS.items())
    try:
        # allow_redirects defaults to True, but it's better to be explicit
        result = requests.get(random.choice(PORTAL_DETECT_URLS), allow_redirects=True)
    except requests.RequestException:
        print("Network error, probably offline")
        return
    if result.text.strip() == expected_content:
        print("Computer is online")
        return
    print("Did not match expected content, trying to log-in.")
    login(result.url, result.text)


def main():
    """Check periodically if the computer is online."""
    print("autologin started")
    # TODO really load config
    config = {"ulco": ("login", "password")}

    while True:
        sleep(CHECK_PERIOD.total_seconds())
        check_online(config)


if __name__ == "__main__":
    main()
