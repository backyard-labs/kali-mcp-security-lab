import sys
import json

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.mark.anyio
async def test_mcp_client_connects_and_lists_registered_tools():
    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=["kali_lab_server.py"],
    )

    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            initialize_result = await session.initialize()
            tools_result = await session.list_tools()

    tool_names = {tool.name for tool in tools_result.tools}

    assert initialize_result.server_info is not None
    assert tool_names == {
        "show_scope_policy",
        "validate_target",
        "discover_hosts",
        "scan_common_ports",
    }


@pytest.mark.anyio
async def test_mcp_safe_tools_return_expected_results():
    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=["kali_lab_server.py"],
    )

    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            policy_result = await session.call_tool(
                "show_scope_policy",
                arguments={},
            )
            accepted_result = await session.call_tool(
                "validate_target",
                arguments={"target": "10.10.10.101"},
            )
            rejected_result = await session.call_tool(
                "validate_target",
                arguments={"target": "192.168.93.1"},
            )

    assert policy_result.is_error is False
    assert accepted_result.is_error is False
    assert rejected_result.is_error is False

    policy = json.loads(policy_result.content[0].text)
    accepted = json.loads(accepted_result.content[0].text)
    rejected = json.loads(rejected_result.content[0].text)

    assert policy == {
        "authorized_network": "10.10.10.0/24",
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

    assert accepted == {
        "authorized": True,
        "target": "10.10.10.101",
        "authorized_network": "10.10.10.0/24",
    }

    assert rejected == {
        "authorized": False,
        "target": "192.168.93.1",
        "authorized_network": "10.10.10.0/24",
        "reason": (
            "Rejected target: Target must be inside 10.10.10.0/24."
        ),
    }
