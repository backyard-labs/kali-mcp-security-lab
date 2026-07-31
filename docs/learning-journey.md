# Learning Journey

This project was built as a sequence of security and engineering decisions, not as a one-command deployment.

## 1. Begin With Authority

The first question was not which Kali tools to expose. It was what authority an AI client should have.

The project chose one isolated network, `10.10.10.0/24`, and a small set of read-oriented operations. This made the trust boundary concrete before implementation began.

Key lesson: define scope and prohibited behavior before designing tool schemas.

## 2. Prefer Narrow Tools

Instead of exposing a shell or a generic Nmap wrapper, the server offers task-specific tools:

- Validate a target.
- Discover hosts on the authorized subnet.
- Scan a fixed set of common TCP ports on one authorized host.

The user supplies a target, not a command. The server constructs the command.

Key lesson: a narrow tool is easier to reason about, authorize, test, and audit than a flexible tool with a long denylist.

## 3. Make Results Structured

Nmap produces XML for the port-scan path. The server parses it into a stable list of `{port, protocol}` objects and rejects malformed or unexpected results.

Key lesson: structured data gives an AI client less ambiguity than terminal output and makes automated validation practical.

## 4. Test the Security Boundary

The suite does more than test successful scans. It exercises:

- Out-of-scope networks and hosts
- IPv6 targets
- Network and broadcast addresses
- Multi-host port-scan attempts
- Malformed Nmap XML
- Unexpected open ports
- Timeouts and process failures
- Audit-write failures
- MCP tool discovery and invocation

Key lesson: security tests should spend substantial effort on rejection paths and failure behavior.

## 5. Validate the Protocol

Unit tests proved the Python behavior. MCP integration tests then proved that a client could initialize a session, list tools, and invoke them with structured arguments.

Key lesson: a correct function is not yet a validated integration. Test the protocol boundary too.

## 6. Perform a Controlled Real Scan

The final validation used MCP Inspector to:

1. Display the active scope policy.
2. Discover hosts on `10.10.10.0/24`.
3. Scan the fixed common-port list on `10.10.10.101`.
4. Confirm the structured result.
5. Confirm the matching JSONL audit event.

Key lesson: an end-to-end test should connect the client action to the enforcement decision, real execution, returned result, and audit evidence.

## 7. Troubleshoot From Evidence

Firefox showed Inspector stuck at **Connecting...**, but server processes and logs were healthy. The browser's Network panel revealed aborted event connections. Chromium then connected with the same server and tokenized URL.

Key lesson: isolate layers before modifying code. The visible symptom was in the UI, but the evidence separated browser behavior from MCP server behavior.

## Completion Criteria

The version 1 milestone was considered complete only after:

- 36 automated tests passed.
- Inspector connected successfully.
- The server displayed the correct policy.
- A real authorized discovery completed.
- A real fixed-port scan completed.
- Audit events recorded the enforced commands and outcomes.
- Source, tests, and user documentation were checkpointed.

That definition of done turns a working demo into a repeatable learning artifact.
