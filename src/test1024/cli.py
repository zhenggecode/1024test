"""Student-facing commands. All results come from the background service."""

import argparse
import getpass
import json
import logging
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import ConfigError, client_port


def request(port, path, payload=None):
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    req = Request(
        f"http://127.0.0.1:{port}{path}",
        data=body,
        headers={"Content-Type": "application/json"} if body else {},
    )
    try:
        with urlopen(req, timeout=4) as response:
            return json.load(response)
    except HTTPError as exc:
        try:
            message = json.load(exc).get("error", "request failed")
        except (ValueError, OSError):
            message = "request failed"
        raise RuntimeError(message) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise RuntimeError("无法执行：1024test 服务未运行或无法连接") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(prog="1024test")
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("-m", metavar="USER", help="create an account")
    action.add_argument("-l", metavar="USER", help="log in")
    action.add_argument("-v", action="store_true", help="check the background service")
    parser.add_argument("password", nargs="?", help="password for -m")
    args = parser.parse_args(argv)
    if args.password is not None and args.m is None:
        parser.error("a password argument is only allowed with -m")
    if args.m is not None and args.password is None:
        parser.error("-m requires a password")
    try:
        port = client_port()
        if args.v:
            print(request(port, "/health")["status"])
        elif args.m is not None:
            result = request(port, "/create", {"username": args.m, "password": args.password})
            if not result["created"]:
                print("用户已存在", file=sys.stderr)
                return 1
            print("true")
        else:
            if not request(port, "/exists", {"username": args.l})["exists"]:
                print("无该用户")
                return 1
            password = getpass.getpass("password：")
            result = request(port, "/login", {"username": args.l, "password": password})
            if result["result"] == "missing":
                print("无该用户")
                return 1
            if result["result"] != "ok":
                print("密码错误")
                return 1
            print("logining")
    except (ConfigError, RuntimeError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except Exception:
        logging.exception("unexpected client error")
        print("无法执行：客户端发生未处理错误", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
