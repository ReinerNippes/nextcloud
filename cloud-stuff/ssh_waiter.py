"""Dynamic resource provider that waits for SSH connectivity."""

import socket
import time
from typing import Any, Dict, Optional

import pulumi
from pulumi import ResourceOptions
from pulumi.dynamic import (
    CheckFailure,
    CheckResult,
    CreateResult,
    DiffResult,
    Resource,
    ResourceProvider,
    UpdateResult,
)


class _SshWaiterProvider(ResourceProvider):
    def check(self, _olds: Dict[str, Any], news: Dict[str, Any]) -> CheckResult:
        failures = []
        if not news.get("ip"):
            failures.append(CheckFailure(property_="ip", reason="is required"))
        return CheckResult(inputs=news, failures=failures)

    def diff(self, _id: str, olds: Dict[str, Any], news: Dict[str, Any]) -> DiffResult:
        return DiffResult(changes=olds.get("ip") != news.get("ip"))

    def _wait(self, ip: str, timeout: int) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                sock = socket.create_connection((ip, 22), timeout=5)
                sock.close()
                return
            except (socket.error, OSError):
                time.sleep(5)
        raise TimeoutError(f"Server {ip} not reachable on port 22 after {timeout}s")

    def create(self, props: Dict[str, Any]) -> CreateResult:
        self._wait(props["ip"], int(props.get("timeout", 300)))
        return CreateResult(id_=props["ip"], outs=props)

    def update(self, _id: str, _olds: Dict[str, Any], news: Dict[str, Any]) -> UpdateResult:
        self._wait(news["ip"], int(news.get("timeout", 300)))
        return UpdateResult(outs=news)

    def delete(self, _id: str, _props: Dict[str, Any]) -> None:
        pass


class SshWaiter(Resource):
    def __init__(
        self,
        name: str,
        ip: pulumi.Input[str],
        timeout: int = 300,
        opts: Optional[ResourceOptions] = None,
    ):
        super().__init__(
            _SshWaiterProvider(),
            name,
            {"ip": ip, "timeout": timeout},
            opts,
        )
