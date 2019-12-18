#!usr/bin/env python

import configparser
import imaplib
import os
import select
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict


class Encryption(Enum):
    NONE = auto()
    IMAPS = auto()
    STARTTLS = auto()


@dataclass
class Configuration:
    """Holds application configuration"""

    host: str
    port: int
    username: str
    password: str
    encryption: Encryption
    debug: bool


class ImapError(Exception):
    pass


class ConfigError(ImapError):
    pass


def get_password(section: configparser.SectionProxy) -> str:
    password = section.get("password", None)
    password_cmd = section.get("password_command", None)
    if password and password_cmd:
        raise ConfigError("password or password_command are mutually exclusive")
    elif password_cmd:
        process = subprocess.run(password_cmd, capture_output=True, shell=True)
        if process.returncode != 0:
            raise ConfigError(
                f"Password command '{password_cmd}' exited with {process.returncode}"
            )
        password = process.stdout.decode("utf-8").rstrip()
    elif not password:
        raise ConfigError("No imap password or password_command set")
    return password


def get_encryption(section: configparser.SectionProxy) -> Encryption:
    imaps = section.getboolean("imaps", fallback=False)
    starttls = section.getboolean("starttls", fallback=not imaps)
    if starttls and imaps:
        raise ImapError(f"You cannot enable both starttls and imaps")
    if imaps:
        return Encryption.IMAPS
    if starttls:
        return Encryption.STARTTLS
    return Encryption.NONE


def get_port(section: configparser.SectionProxy, default_port: int) -> int:
    raw_port = section.get("port", str(default_port))
    try:
        port = int(raw_port)
        if port not in range(1, 65535):
            raise ImapError(f"Imap port is out of range (1-65535): {port}")
        return port
    except ValueError as err:
        raise ImapError(f"Imap port is not a valid: {port}: {err}")


def read_configuration(path: str) -> Configuration:
    parser = configparser.ConfigParser()
    parser.read(path)
    if "imap" not in parser:
        raise ConfigError("No imap section found")
    imap = parser["imap"]

    host = imap.get("host", None)
    if not host:
        raise ConfigError("No imap host set")

    username = imap.get("username", None)
    if not username:
        raise ConfigError("No imap username set")

    encryption = get_encryption(imap)

    return Configuration(
        host=host,
        port=get_port(imap, 993 if encryption == Encryption.IMAPS else 143),
        username=username,
        password=get_password(imap),
        encryption=encryption,
        debug=imap.getboolean("debug", fallback=False),
    )


def connect(config: Configuration) -> imaplib.IMAP4:
    if config.encryption != Encryption.IMAPS:
        imapclass = imaplib.IMAP4
    else:
        imapclass = imaplib.IMAP4_SSL

    client = imapclass(host=config.host, port=config.port)
    client.debug = 4 if config.debug else 0
    if config.encryption == Encryption.STARTTLS:
        client.starttls()

    # rv, data = client.login(config.username, config.password)
    client.login(config.username, config.password)
    return client


def wait_for_change(config: Configuration) -> None:
    backoff = 0

    while True:
        time.sleep(backoff)
        try:
            client = connect(config)
        except OSError as err:
            backoff = min(120, 2 * max(1, backoff))
            print(
                f"Could not connect to server: {err}. Retry in {backoff} sec",
                file=sys.stderr,
            )
            continue
        backoff = 0
        print("connected")
        typ, dat = client._simple_command(
            "NOTIFY SET",
            "(subscribed (FlagChange SubscriptionChange MessageNew MessageExpunge))",
        )
        rlist, _, _ = select.select([client.socket()], [], [], 60 * 15)
        if len(rlist) != 0:
            print("Got change")
        else:
            print("Timeout")
        break


def main() -> None:
    # monkey patch imaplib to support NOTIFY SET
    imaplib.Commands["NOTIFY SET"] = ("AUTH",)  # type: ignore

    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_home = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        config_file = os.path.join(config_home, "imap-notify", "imap-notify.ini")

    try:
        config = read_configuration(config_file)
    except ConfigError as e:
        print(f"Error reading configuration: {e}")
        sys.exit(1)

    wait_for_change(config)


if __name__ == "__main__":
    main()
