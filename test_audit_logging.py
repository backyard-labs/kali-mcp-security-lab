import json
from datetime import datetime

import pytest

import kali_lab_server as server


@pytest.fixture
def isolated_audit_log(tmp_path, monkeypatch):
    """Redirect audit events to an isolated temporary file."""
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(server, "AUDIT_LOG_PATH", audit_path)
    return audit_path


def read_audit_events(audit_path):
    """Read every JSONL audit event from the temporary log."""
    return [
        json.loads(line)
        for line in audit_path.read_text(encoding="utf-8").splitlines()
    ]


def assert_common_event_fields(event):
    """Verify the fields required in every audit record."""
    assert set(event) == {
        "timestamp_utc",
        "tool",
        "target",
        "authorized",
        "command",
        "exit_code",
        "duration_ms",
    }

    timestamp = datetime.fromisoformat(event["timestamp_utc"])
    assert timestamp.tzinfo is not None

    assert isinstance(event["duration_ms"], (int, float))
    assert event["duration_ms"] >= 0


def test_authorized_and_rejected_targets_are_logged(isolated_audit_log):
    accepted = server.validate_target("10.10.10.101")
    rejected = server.validate_target("192.168.93.1")

    assert accepted["authorized"] is True
    assert rejected["authorized"] is False

    events = read_audit_events(isolated_audit_log)

    assert len(events) == 2

    accepted_event, rejected_event = events

    assert_common_event_fields(accepted_event)
    assert accepted_event["tool"] == "validate_target"
    assert accepted_event["target"] == "10.10.10.101"
    assert accepted_event["authorized"] is True
    assert accepted_event["command"] is None
    assert accepted_event["exit_code"] is None

    assert_common_event_fields(rejected_event)
    assert rejected_event["tool"] == "validate_target"
    assert rejected_event["target"] == "192.168.93.1"
    assert rejected_event["authorized"] is False
    assert rejected_event["command"] is None
    assert rejected_event["exit_code"] is None


def test_discovery_command_and_exit_code_are_logged(
    isolated_audit_log,
    monkeypatch,
):
    class CompletedProcess:
        returncode = 0
        stdout = "Nmap scan report for 10.10.10.101"
        stderr = ""

    monkeypatch.setattr(
        server.subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcess(),
    )

    result = server.discover_hosts("10.10.10.0/24")

    assert result["authorized"] is True
    assert result["exit_code"] == 0

    events = read_audit_events(isolated_audit_log)
    assert len(events) == 1

    event = events[0]
    assert_common_event_fields(event)

    assert event["tool"] == "discover_hosts"
    assert event["target"] == "10.10.10.0/24"
    assert event["authorized"] is True
    assert event["exit_code"] == 0
    assert event["command"] == [
        "/usr/bin/nmap",
        "-sn",
        "-n",
        "--max-retries",
        "1",
        "--host-timeout",
        "10s",
        "10.10.10.0/24",
    ]


def test_common_port_scan_command_and_results_are_logged(
    isolated_audit_log,
    monkeypatch,
):
    class CompletedProcess:
        returncode = 0
        stdout = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open"/>
      </port>
      <port protocol="tcp" portid="443">
        <state state="open"/>
      </port>
    </ports>
  </host>
</nmaprun>
"""
        stderr = ""

    monkeypatch.setattr(
        server.subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcess(),
    )

    result = server.scan_common_ports("10.10.10.101")

    assert result["authorized"] is True
    assert result["exit_code"] == 0
    assert result["open_ports"] == [
        {"port": 22, "protocol": "tcp"},
        {"port": 443, "protocol": "tcp"},
    ]

    events = read_audit_events(isolated_audit_log)
    assert len(events) == 1

    event = events[0]
    assert_common_event_fields(event)

    assert event["tool"] == "scan_common_ports"
    assert event["target"] == "10.10.10.101"
    assert event["authorized"] is True
    assert event["exit_code"] == 0
    assert event["command"][0:4] == [
        "/usr/bin/nmap",
        "-sT",
        "-n",
        "-Pn",
    ]
    assert event["command"][-1] == "10.10.10.101"
    assert "-sV" not in event["command"]
    assert "--script" not in event["command"]


def test_discovery_timeout_logs_null_exit_code(
    isolated_audit_log,
    monkeypatch,
):
    def raise_timeout(*args, **kwargs):
        raise server.subprocess.TimeoutExpired(
            cmd=args[0],
            timeout=server.NMAP_TIMEOUT_SECONDS,
        )

    monkeypatch.setattr(server.subprocess, "run", raise_timeout)

    result = server.discover_hosts("10.10.10.0/24")

    assert result["authorized"] is True
    assert "timeout" in result["error"].lower()

    events = read_audit_events(isolated_audit_log)
    assert len(events) == 1

    event = events[0]
    assert_common_event_fields(event)

    assert event["tool"] == "discover_hosts"
    assert event["authorized"] is True
    assert event["command"] is not None
    assert event["exit_code"] is None


def test_rejected_scan_does_not_construct_or_run_nmap(
    isolated_audit_log,
    monkeypatch,
):
    def unexpected_run(*args, **kwargs):
        pytest.fail("Nmap must not run for an unauthorized target.")

    monkeypatch.setattr(server.subprocess, "run", unexpected_run)

    result = server.scan_common_ports("192.168.93.1")

    assert result["authorized"] is False

    events = read_audit_events(isolated_audit_log)
    assert len(events) == 1

    event = events[0]
    assert_common_event_fields(event)

    assert event["tool"] == "scan_common_ports"
    assert event["target"] == "192.168.93.1"
    assert event["authorized"] is False
    assert event["command"] is None
    assert event["exit_code"] is None


def test_audit_write_failure_does_not_break_safe_tool(
    tmp_path,
    monkeypatch,
):
    # A directory cannot be opened as an appendable JSONL file.
    unwritable_log_target = tmp_path / "audit-directory"
    unwritable_log_target.mkdir()

    monkeypatch.setattr(
        server,
        "AUDIT_LOG_PATH",
        unwritable_log_target,
    )

    result = server.show_scope_policy()

    assert result["authorized_network"] == "10.10.10.0/24"
    assert "permitted_operations" in result
    assert "prohibited_capabilities" in result
