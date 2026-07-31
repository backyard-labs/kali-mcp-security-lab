import pytest
import subprocess
import kali_lab_server as server
from kali_lab_server import normalize_authorized_host, parse_open_ports


def test_parse_open_ports_filters_and_sorts_results():
    xml = """<nmaprun>
    <host>
    <ports>
    <port protocol="tcp" portid="445"><state state="open"/></port>
    <port protocol="tcp" portid="22"><state state="closed"/></port>
    <port protocol="udp" portid="53"><state state="open"/></port>
    <port protocol="tcp" portid="80"><state state="open"/></port>
    <port protocol="tcp" portid="21"><state state="open"/></port>
    </ports>
    </host>
    </nmaprun>"""

    assert parse_open_ports(xml) == [
        {"port": 21, "protocol": "tcp"},
        {"port": 80, "protocol": "tcp"},
        {"port": 445, "protocol": "tcp"},
    ]


def test_parse_open_ports_rejects_malformed_xml():
    with pytest.raises(
        ValueError,
        match=r"^Nmap returned malformed XML output\.$",
    ):
        parse_open_ports("<invalid-nmap-xml")


def test_parse_open_ports_rejects_port_outside_allowlist():
    xml = """<nmaprun>
    <host>
    <ports>
    <port protocol="tcp" portid="9999"><state state="open"/></port>
    </ports>
    </host>
    </nmaprun>"""

    with pytest.raises(
        ValueError,
        match=r"^Nmap XML contained a port outside the fixed allowlist\.$",
    ):
        parse_open_ports(xml)


def test_parse_open_ports_rejects_invalid_port_number():
    xml = """<nmaprun>
    <host>
    <ports>
    <port protocol="tcp" portid="not-a-number">
    <state state="open"/>
    </port>
    </ports>
    </host>
    </nmaprun>"""

    with pytest.raises(
        ValueError,
        match=r"^Nmap XML contained an invalid port number\.$",
    ):
        parse_open_ports(xml)


def test_parse_open_ports_returns_empty_list_when_none_are_open():
    xml = """<nmaprun>
    <host>
    <ports>
    <port protocol="tcp" portid="22"><state state="closed"/></port>
    <port protocol="tcp" portid="80"><state state="filtered"/></port>
    </ports>
    </host>
    </nmaprun>"""

    assert parse_open_ports(xml) == []
def test_normalize_authorized_host_accepts_valid_in_scope_host():
    assert normalize_authorized_host("10.10.10.101") == "10.10.10.101"


def test_normalize_authorized_host_strips_whitespace():
    assert normalize_authorized_host("  10.10.10.101  ") == "10.10.10.101"


@pytest.mark.parametrize(
    ("target", "expected_message"),
    [
        (
            "10.10.10.0/24",
            "Rejected target: scan_common_ports accepts one IPv4 host, "
            "not a subnet or CIDR target.",
        ),
        (
            "192.168.93.1",
            "Rejected target: Target must be inside 10.10.10.0/24.",
        ),
        (
            "10.10.10.0",
            "Rejected target: The network address is not a host.",
        ),
        (
            "10.10.10.255",
            "Rejected target: The broadcast address is not a host.",
        ),
        (
            "localhost",
            "Rejected target: A valid IPv4 host address is required.",
        ),
        (
            "::1",
            "Rejected target: Only IPv4 hosts are permitted.",
        ),
    ],
)
def test_normalize_authorized_host_rejects_invalid_targets(
    target,
    expected_message,
):
    with pytest.raises(ValueError) as exc_info:
        normalize_authorized_host(target)

    assert str(exc_info.value) == expected_message
def test_scan_common_ports_returns_structured_results(monkeypatch):
    xml = """<nmaprun>
    <host>
    <ports>
    <port protocol="tcp" portid="445"><state state="open"/></port>
    <port protocol="tcp" portid="22"><state state="closed"/></port>
    <port protocol="tcp" portid="80"><state state="open"/></port>
    <port protocol="tcp" portid="21"><state state="open"/></port>
    </ports>
    </host>
    </nmaprun>"""

    recorded_call = {}

    def fake_run(command, **kwargs):
        recorded_call["command"] = command
        recorded_call["kwargs"] = kwargs

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=xml,
            stderr="",
        )

    monkeypatch.setattr(server.subprocess, "run", fake_run)

    result = server.scan_common_ports("10.10.10.101")

    expected_ports = [
        {"port": 21, "protocol": "tcp"},
        {"port": 80, "protocol": "tcp"},
        {"port": 445, "protocol": "tcp"},
    ]

    assert result == {
        "authorized": True,
        "target": "10.10.10.101",
        "scan_type": "TCP connect scan",
        "ports_tested": list(server.COMMON_TCP_PORTS),
        "open_port_count": 3,
        "open_ports": expected_ports,
        "command_policy": (
            "Fixed common-port allowlist; one host only; "
            "no custom options, scripts, or service detection"
        ),
        "exit_code": 0,
        "stderr": "",
    }

    port_specification = ",".join(
        str(port) for port in server.COMMON_TCP_PORTS
    )

    assert recorded_call["command"] == [
        "/usr/bin/nmap",
        "-sT",
        "-n",
        "-Pn",
        "--open",
        "--max-retries",
        "1",
        "--host-timeout",
        "30s",
        "-p",
        port_specification,
        "-oX",
        "-",
        "10.10.10.101",
    ]

    assert recorded_call["kwargs"] == {
        "capture_output": True,
        "text": True,
        "timeout": server.NMAP_TIMEOUT_SECONDS,
        "check": False,
    }


def test_scan_common_ports_rejects_target_without_running_nmap(monkeypatch):
    def unexpected_run(*args, **kwargs):
        pytest.fail("subprocess.run must not be called for a rejected target")

    monkeypatch.setattr(server.subprocess, "run", unexpected_run)

    result = server.scan_common_ports("192.168.93.1")

    assert result == {
        "authorized": False,
        "target": "192.168.93.1",
        "error": "Rejected target: Target must be inside 10.10.10.0/24.",
    }


def test_scan_common_ports_handles_timeout(monkeypatch):
    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd=command,
            timeout=kwargs["timeout"],
        )

    monkeypatch.setattr(server.subprocess, "run", fake_run)

    result = server.scan_common_ports("10.10.10.101")

    assert result == {
        "authorized": True,
        "target": "10.10.10.101",
        "ports_tested": list(server.COMMON_TCP_PORTS),
        "error": "Common-port scan exceeded the enforced timeout.",
    }


def test_scan_common_ports_handles_nmap_failure(monkeypatch):
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            args=command,
            returncode=2,
            stdout="",
            stderr="Nmap failed",
        )

    monkeypatch.setattr(server.subprocess, "run", fake_run)

    result = server.scan_common_ports("10.10.10.101")

    assert result == {
        "authorized": True,
        "target": "10.10.10.101",
        "ports_tested": list(server.COMMON_TCP_PORTS),
        "exit_code": 2,
        "error": "Nmap common-port scan failed.",
        "stderr": "Nmap failed",
    }


def test_scan_common_ports_handles_malformed_xml(monkeypatch):
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="<invalid-nmap-xml",
            stderr="",
        )

    monkeypatch.setattr(server.subprocess, "run", fake_run)

    result = server.scan_common_ports("10.10.10.101")

    assert result == {
        "authorized": True,
        "target": "10.10.10.101",
        "ports_tested": list(server.COMMON_TCP_PORTS),
        "exit_code": 0,
        "error": "Nmap returned malformed XML output.",
        "stderr": "",
    }


def test_scan_common_ports_returns_zero_when_no_ports_are_open(monkeypatch):
    xml = """<nmaprun>
    <host>
    <ports>
    <port protocol="tcp" portid="22"><state state="closed"/></port>
    <port protocol="tcp" portid="80"><state state="filtered"/></port>
    </ports>
    </host>
    </nmaprun>"""

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout=xml,
            stderr="",
        )

    monkeypatch.setattr(server.subprocess, "run", fake_run)

    result = server.scan_common_ports("10.10.10.101")

    assert result["authorized"] is True
    assert result["target"] == "10.10.10.101"
    assert result["ports_tested"] == list(server.COMMON_TCP_PORTS)
    assert result["open_port_count"] == 0
    assert result["open_ports"] == []
    assert result["exit_code"] == 0
    assert result["stderr"] == ""


def test_show_scope_policy_reports_enforced_restrictions():
    result = server.show_scope_policy()

    assert result["authorized_network"] == "10.10.10.0/24"

    assert "Run fixed Nmap host discovery" in result["permitted_operations"]
    assert (
        "Scan a fixed list of common TCP ports on one IPv4 host"
        in result["permitted_operations"]
    )

    assert (
        "Targets outside the authorized network"
        in result["prohibited_capabilities"]
    )
    assert "Arbitrary shell commands" in result["prohibited_capabilities"]
    assert "User-supplied Nmap options" in result["prohibited_capabilities"]
    assert "Service enumeration" in result["prohibited_capabilities"]
    assert "Exploitation" in result["prohibited_capabilities"]
    assert "Nmap scripts" in result["prohibited_capabilities"]


def test_validate_target_accepts_in_scope_host():
    assert server.validate_target("10.10.10.101") == {
        "authorized": True,
        "target": "10.10.10.101",
        "authorized_network": "10.10.10.0/24",
    }


def test_validate_target_canonicalizes_in_scope_subnet():
    assert server.validate_target("10.10.10.25/24") == {
        "authorized": True,
        "target": "10.10.10.0/24",
        "authorized_network": "10.10.10.0/24",
    }


@pytest.mark.parametrize(
    ("target", "expected_reason"),
    [
        (
            "192.168.93.1",
            "Rejected target: Target must be inside 10.10.10.0/24.",
        ),
        (
            "::1",
            "Rejected target: Only IPv4 targets are permitted.",
        ),
    ],
)
def test_validate_target_rejects_unauthorized_targets(
    target,
    expected_reason,
):
    assert server.validate_target(target) == {
        "authorized": False,
        "target": target,
        "authorized_network": "10.10.10.0/24",
        "reason": expected_reason,
    }


def test_discover_hosts_uses_fixed_command(monkeypatch):
    recorded_call = {}

    def fake_run(command, **kwargs):
        recorded_call["command"] = command
        recorded_call["kwargs"] = kwargs

        return subprocess.CompletedProcess(
            args=command,
            returncode=0,
            stdout="Nmap scan report for 10.10.10.101\nHost is up.\n",
            stderr="",
        )

    monkeypatch.setattr(server.subprocess, "run", fake_run)

    result = server.discover_hosts("10.10.10.0/24")

    assert result == {
        "authorized": True,
        "target": "10.10.10.0/24",
        "command_policy": (
            "Fixed Nmap host discovery; no user options accepted"
        ),
        "exit_code": 0,
        "stdout": (
            "Nmap scan report for 10.10.10.101\nHost is up."
        ),
        "stderr": "",
    }

    assert recorded_call["command"] == [
        "/usr/bin/nmap",
        "-sn",
        "-n",
        "--max-retries",
        "1",
        "--host-timeout",
        "10s",
        "10.10.10.0/24",
    ]

    assert recorded_call["kwargs"] == {
        "capture_output": True,
        "text": True,
        "timeout": server.NMAP_TIMEOUT_SECONDS,
        "check": False,
    }


def test_discover_hosts_rejects_target_without_running_nmap(monkeypatch):
    def unexpected_run(*args, **kwargs):
        pytest.fail("subprocess.run must not run for an unauthorized target")

    monkeypatch.setattr(server.subprocess, "run", unexpected_run)

    result = server.discover_hosts("192.168.93.0/24")

    assert result == {
        "authorized": False,
        "target": "192.168.93.0/24",
        "error": (
            "Rejected target: Target must be inside 10.10.10.0/24."
        ),
    }


def test_discover_hosts_handles_timeout(monkeypatch):
    def fake_run(command, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd=command,
            timeout=kwargs["timeout"],
        )

    monkeypatch.setattr(server.subprocess, "run", fake_run)

    result = server.discover_hosts("10.10.10.0/24")

    assert result == {
        "authorized": True,
        "target": "10.10.10.0/24",
        "error": "Host discovery exceeded the enforced timeout.",
    }


def test_discover_hosts_reports_nonzero_exit(monkeypatch):
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            args=command,
            returncode=2,
            stdout="",
            stderr="Nmap discovery failed\n",
        )

    monkeypatch.setattr(server.subprocess, "run", fake_run)

    result = server.discover_hosts("10.10.10.0/24")

    assert result == {
        "authorized": True,
        "target": "10.10.10.0/24",
        "command_policy": (
            "Fixed Nmap host discovery; no user options accepted"
        ),
        "exit_code": 2,
        "stdout": "",
        "stderr": "Nmap discovery failed",
    }
