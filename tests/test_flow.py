import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from test1024 import cli
class ProtocolDouble:
    def __init__(self): self.users = {}; self.running = True
    def __call__(self, _port, path, payload=None):
        if not self.running: raise RuntimeError("无法执行：1024test 服务未运行或无法连接")
        if path == "/health": return {"status": "running"}
        username = payload["username"]
        if path == "/exists": return {"exists": username in self.users}
        if path == "/create":
            if username in self.users: return {"created": False}
            self.users[username] = payload["password"]; return {"created": True}
        if username not in self.users: return {"result": "missing"}
        return {"result": "ok" if self.users[username] == payload["password"] else "wrong"}
class FlowTests(unittest.TestCase):
    def setUp(self):
        self.protocol = ProtocolDouble()
        self.request_patch = patch("test1024.cli.request", side_effect=self.protocol)
        self.port_patch = patch("test1024.cli.client_port", return_value=8024)
        self.request_patch.start(); self.port_patch.start()
    def tearDown(self): self.request_patch.stop(); self.port_patch.stop()
    def run_cli(self, args, password=None):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            if password is None: code = cli.main(args)
            else:
                with patch("test1024.cli.getpass.getpass", return_value=password) as prompt:
                    code = cli.main(args); prompt.assert_called_once_with("password：")
        return code, out.getvalue(), err.getvalue()
    def test_deployment_acceptance_flow(self):
        self.assertEqual(self.run_cli(["-v"]), (0, "running\n", ""))
        self.assertEqual(self.run_cli(["-m", "user", "123456"]), (0, "true\n", ""))
        self.assertEqual(self.run_cli(["-l", "user"], "123456"), (0, "logining\n", ""))
        self.protocol.users.pop("user")
        self.assertEqual(self.run_cli(["-l", "user"]), (1, "无该用户\n", ""))
    def test_stopped_service_blocks_version_check(self):
        self.protocol.running = False
        result = self.run_cli(["-v"])
        self.assertEqual(result[0], 1); self.assertIn("无法执行", result[2])
    def test_duplicate_and_wrong_password(self):
        self.run_cli(["-m", "user", "123456"])
        self.assertEqual(self.run_cli(["-m", "user", "another"])[0], 1)
        self.assertEqual(self.run_cli(["-l", "user"], "wrong"), (1, "密码错误\n", ""))
if __name__ == "__main__": unittest.main()
