import ipaddress
import json
import os
import subprocess
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from mcp.server import MCPServer


mcp = MCPServer("kali-lab-tools")

AUTHORIZED_NETWORK = ipaddress.ip_network("10.10.10.0/24")
NMAP_TIMEOUT_SECONDS = 120

AUDIT_LOG_PATH = Path(
    os.environ.get(
        "KALI_LAB_AUDIT_LOG",
        "kali_lab_audit.jsonl",
    )
)

COMMON_TCP_PORTS = (
    21,    # FTP
    22,    # SSH
    23,    # Telnet
    25,    # SMTP
    53,    # DNS over TCP
    80,    # HTTP
    110,   # POP3
    139,   # NetBIOS session
    443,   # HTTPS
    445,   # SMB
    3306,  # MySQL
    5432,  # PostgreSQL
    5900,  # VNC
    8080,  # Alternate HTTP
)


def audited_result(
    *,
    tool: str,
    target: str | None,
    authorized: bool | None,
    result: dict,
    started_at: float,
    command: list[str] | None = None,
    exit_code: int | None = None,
) -> dict:
    """Write one structured audit event without disrupting tool execution."""
    event = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "target": target,
        "authorized": authorized,
        "command": command,
        "exit_code": exit_code,
        "duration_ms": round(
            (time.monotonic() - started_at) * 1000,
            3,
        ),
    }

    try:
        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as audit_file:
            audit_file.write(
                json.dumps(
                    event,
                    separators=(",", ":"),
                    sort_keys=True,
                )
                + "\n"
            )
    except OSError:
        # Audit-log failures must not interrupt safe tool operation.
        pass

    return result


def normalize_authorized_target(target: str) -> str:
    """Validate and canonicalize an IPv4 host or network."""
    target = target.strip()

    try:
        if "/" in target:
            parsed = ipaddress.ip_network(target, strict=False)

            if parsed.version != 4:
                raise ValueError("Only IPv4 targets are permitted.")

            if not parsed.subnet_of(AUTHORIZED_NETWORK):
                raise ValueError(
                    f"Target must be inside {AUTHORIZED_NETWORK}."
                )

            return str(parsed)

        parsed = ipaddress.ip_address(target)

        if parsed.version != 4:
            raise ValueError("Only IPv4 targets are permitted.")

        if parsed not in AUTHORIZED_NETWORK:
            raise ValueError(
                f"Target must be inside {AUTHORIZED_NETWORK}."
            )

        return str(parsed)

    except ValueError as exc:
        raise ValueError(f"Rejected target: {exc}") from exc


@mcp.tool()
def show_scope_policy() -> dict:
    """Show the server's authorized scope and enforced restrictions."""
    started_at = time.monotonic()

    result = {
        "authorized_network": str(AUTHORIZED_NETWORK),
        "permitted_operations": [
            "Validate an IPv4 host or subnet",
            "Run fixed Nmap host discovery",
            "Scan a fixed list of common TCP ports on one IPv4 host",
        ],
        "prohibited_capabilities": [
            "Targets outside the authorized network",
            "Arbitrary shell commands",
            "User-supplied Nmap options",
            "Subnet or multi-host port scanning",
            "Ports outside the fixed allowlist",
            "Service enumeration",
            "Exploitation",
            "Credential operations",
            "Nmap scripts",
        ],
    }

    return audited_result(
        tool="show_scope_policy",
        target=None,
        authorized=None,
        result=result,
        started_at=started_at,
    )


def normalize_authorized_host(target: str) -> str:
    """Validate one IPv4 host inside the authorized network."""
    target = target.strip()

    if "/" in target:
        raise ValueError(
            "Rejected target: scan_common_ports accepts one IPv4 host, "
            "not a subnet or CIDR target."
        )

    try:
        parsed = ipaddress.ip_address(target)
    except ValueError as exc:
        raise ValueError(
            "Rejected target: A valid IPv4 host address is required."
        ) from exc

    if parsed.version != 4:
        raise ValueError("Rejected target: Only IPv4 hosts are permitted.")

    if parsed not in AUTHORIZED_NETWORK:
        raise ValueError(
            f"Rejected target: Target must be inside {AUTHORIZED_NETWORK}."
        )

    if parsed == AUTHORIZED_NETWORK.network_address:
        raise ValueError("Rejected target: The network address is not a host.")

    if parsed == AUTHORIZED_NETWORK.broadcast_address:
        raise ValueError("Rejected target: The broadcast address is not a host.")

    return str(parsed)


def parse_open_ports(nmap_xml: str) -> list[dict]:
    """Extract open ports from Nmap XML in deterministic numeric order."""
    try:
        root = ET.fromstring(nmap_xml)
    except ET.ParseError as exc:
        raise ValueError("Nmap returned malformed XML output.") from exc

    open_ports = []

    for port_element in root.findall(".//port"):
        state_element = port_element.find("state")

        if state_element is None or state_element.get("state") != "open":
            continue

        protocol = port_element.get("protocol")
        port_text = port_element.get("portid")

        if protocol != "tcp" or port_text is None:
            continue

        try:
            port_number = int(port_text)
        except ValueError as exc:
            raise ValueError(
                "Nmap XML contained an invalid port number."
            ) from exc

        if port_number not in COMMON_TCP_PORTS:
            raise ValueError(
                "Nmap XML contained a port outside the fixed allowlist."
            )

        open_ports.append(
            {
                "port": port_number,
                "protocol": protocol,
            }
        )

    return sorted(open_ports, key=lambda item: item["port"])


@mcp.tool()
def validate_target(target: str) -> dict:
    """Determine whether a target is inside the authorized lab network."""
    started_at = time.monotonic()

    try:
        normalized = normalize_authorized_target(target)
    except ValueError as exc:
        result = {
            "authorized": False,
            "target": target,
            "authorized_network": str(AUTHORIZED_NETWORK),
            "reason": str(exc),
        }

        return audited_result(
            tool="validate_target",
            target=target,
            authorized=False,
            result=result,
            started_at=started_at,
        )

    result = {
        "authorized": True,
        "target": normalized,
        "authorized_network": str(AUTHORIZED_NETWORK),
    }

    return audited_result(
        tool="validate_target",
        target=target,
        authorized=True,
        result=result,
        started_at=started_at,
    )


@mcp.tool()
def discover_hosts(target: str = "10.10.10.0/24") -> dict:
    """Run fixed, nonprivileged Nmap host discovery inside the lab."""
    started_at = time.monotonic()

    try:
        normalized = normalize_authorized_target(target)
    except ValueError as exc:
        result = {
            "authorized": False,
            "target": target,
            "error": str(exc),
        }

        return audited_result(
            tool="discover_hosts",
            target=target,
            authorized=False,
            result=result,
            started_at=started_at,
        )

    command = [
        "/usr/bin/nmap",
        "-sn",
        "-n",
        "--max-retries",
        "1",
        "--host-timeout",
        "10s",
        normalized,
    ]

    try:
        completed_process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=NMAP_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        result = {
            "authorized": True,
            "target": normalized,
            "error": "Host discovery exceeded the enforced timeout.",
        }

        return audited_result(
            tool="discover_hosts",
            target=target,
            authorized=True,
            result=result,
            started_at=started_at,
            command=command,
            exit_code=None,
        )

    result = {
        "authorized": True,
        "target": normalized,
        "command_policy": (
            "Fixed Nmap host discovery; no user options accepted"
        ),
        "exit_code": completed_process.returncode,
        "stdout": completed_process.stdout.strip(),
        "stderr": completed_process.stderr.strip(),
    }

    return audited_result(
        tool="discover_hosts",
        target=target,
        authorized=True,
        result=result,
        started_at=started_at,
        command=command,
        exit_code=completed_process.returncode,
    )


@mcp.tool()
def scan_common_ports(target: str) -> dict:
    """Scan a fixed list of common TCP ports on one authorized lab host."""
    started_at = time.monotonic()

    try:
        normalized = normalize_authorized_host(target)
    except ValueError as exc:
        result = {
            "authorized": False,
            "target": target,
            "error": str(exc),
        }

        return audited_result(
            tool="scan_common_ports",
            target=target,
            authorized=False,
            result=result,
            started_at=started_at,
        )

    port_specification = ",".join(
        str(port) for port in COMMON_TCP_PORTS
    )

    command = [
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
        normalized,
    ]

    try:
        completed_process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=NMAP_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        result = {
            "authorized": True,
            "target": normalized,
            "ports_tested": list(COMMON_TCP_PORTS),
            "error": "Common-port scan exceeded the enforced timeout.",
        }

        return audited_result(
            tool="scan_common_ports",
            target=target,
            authorized=True,
            result=result,
            started_at=started_at,
            command=command,
            exit_code=None,
        )

    if completed_process.returncode != 0:
        result = {
            "authorized": True,
            "target": normalized,
            "ports_tested": list(COMMON_TCP_PORTS),
            "exit_code": completed_process.returncode,
            "error": "Nmap common-port scan failed.",
            "stderr": completed_process.stderr.strip(),
        }

        return audited_result(
            tool="scan_common_ports",
            target=target,
            authorized=True,
            result=result,
            started_at=started_at,
            command=command,
            exit_code=completed_process.returncode,
        )

    try:
        open_ports = parse_open_ports(completed_process.stdout)
    except ValueError as exc:
        result = {
            "authorized": True,
            "target": normalized,
            "ports_tested": list(COMMON_TCP_PORTS),
            "exit_code": completed_process.returncode,
            "error": str(exc),
            "stderr": completed_process.stderr.strip(),
        }

        return audited_result(
            tool="scan_common_ports",
            target=target,
            authorized=True,
            result=result,
            started_at=started_at,
            command=command,
            exit_code=completed_process.returncode,
        )

    result = {
        "authorized": True,
        "target": normalized,
        "scan_type": "TCP connect scan",
        "ports_tested": list(COMMON_TCP_PORTS),
        "open_port_count": len(open_ports),
        "open_ports": open_ports,
        "command_policy": (
            "Fixed common-port allowlist; one host only; "
            "no custom options, scripts, or service detection"
        ),
        "exit_code": completed_process.returncode,
        "stderr": completed_process.stderr.strip(),
    }

    return audited_result(
        tool="scan_common_ports",
        target=target,
        authorized=True,
        result=result,
        started_at=started_at,
        command=command,
        exit_code=completed_process.returncode,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
