"""Shared project defaults and service labels."""

DEFAULT_HOST = "172.16.54.18"
DEFAULT_SERVICE = "DX"

WATCH_INTERVAL = 10
CHECK_TIMEOUT = 3.0

SERVICE_MENU = {"1": "DX", "2": "YD", "3": "LT", "4": "校园网"}
SERVICE_NAMES = {"DX": "电信", "YD": "移动", "LT": "联通", "校园网": "校园网"}
SERVICE_VALUES = {"电信": "DX", "移动": "YD", "联通": "LT", "校园网": "校园网"}
VALID_SERVICES = set(SERVICE_NAMES)
