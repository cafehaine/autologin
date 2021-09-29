from abc import ABC, abstractmethod
from argparse import ArgumentParser
from configparser import ConfigParser
from datetime import timedelta
import os
import random
import sys
from time import sleep
from typing import Dict, Type

import requests

# Urls and contents used to check if we are blocked
PORTAL_DETECT_URLS: Dict[str, str] = {
    "http://detectportal.firefox.com/canonical.html": '<meta http-equiv="refresh" content="0;url=https://support.mozilla.org/kb/captive-portal"/>',
    "http://nmcheck.gnome.org/check_network_status.txt": "NetworkManager is online",
    "http://ping.archlinux.org/": "This domain is used for connectivity checking (captive portal detection).",
}

CHECK_PERIOD = timedelta(seconds=60)

CONFIG_EXPECTED_PATHS = [
    "~/.config/autologin/config.ini",
    "~/.autologin.ini",
    "/etc/autologin.ini",
]


class PortalHandler(ABC):
    def __init__(self, config: ConfigParser) -> None:
        self._config = config

    @abstractmethod
    def login(self, url: str, portal: str) -> None:
        ...


class ULCOPortalHandler(PortalHandler):
    def login(self, url: str, portal: str) -> None:
        pass  # TODO actually do the requests to login


def get_portal_handler(url: str, portal: str) -> Type[PortalHandler]:
    """Return a PortalHandler based on the portal's contents."""
    # TODO detect portal, for now only support for ULCO's portal
    return ULCOPortalHandler


def login(config: ConfigParser, url: str, portal: str) -> None:
    """Select a portal handler, and then call the login method."""
    portal_handler = get_portal_handler(url, portal)
    print(f"Detected portal of type {portal_handler.__class__.__name__}.")
    portal_handler(config).login(url, portal)


def check_online(config: ConfigParser) -> None:
    """Check if the computer is online, and login if a portal is detected."""
    url, expected_content = random.choice(list(PORTAL_DETECT_URLS.items()))
    try:
        # allow_redirects defaults to True, but it's better to be explicit
        result = requests.get(url, allow_redirects=True)
    except requests.RequestException:
        print("Network error, probably offline")
        return
    if result.text.strip() == expected_content:
        print("Computer is online")
        return
    print("Did not match expected content, trying to log-in.")
    login(config, result.url, result.text)


def load_config(path: str) -> ConfigParser:
    """Load a config from a given path."""
    config = ConfigParser()
    config.read(path)
    return config


def main():
    """Check periodically if the computer is online."""
    parser = ArgumentParser()
    parser.add_argument("--configuration-path", "-c", nargs=1, type=str, default=None)

    args = parser.parse_args()

    config: Optional[ConfigParser] = None

    if args.configuration_path is not None:
        path = args.configuration_path[0]
        if not os.path.exists(path):
            print(f"Config file {path!r} not found.")
            sys.exit(1)
        config = load_config(path)
    else:
        for path in CONFIG_EXPECTED_PATHS:
            if os.path.exists(path):
                config = load_config(path)
                break

    if config is None:
        print(
            "Could not find any configuration file, please create one at one of the expected paths, or pass it as an argument."
        )
        print("Expected paths are the following:")
        for path in CONFIG_EXPECTED_PATHS:
            print("-", path)
        sys.exit(1)

    print("autologin started")

    sleep_duration = config.getint(
        "general", "update_period", fallback=CHECK_PERIOD.total_seconds()
    )

    while True:
        print(f"Waiting for {sleep_duration}s before checking.")
        sleep(sleep_duration)
        check_online(config)


if __name__ == "__main__":
    main()
