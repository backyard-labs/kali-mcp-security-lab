# Contributing to Kali MCP Security Lab

Thank you for your interest in contributing to Kali MCP Security Lab.

This repository is an experimental educational project for studying how an MCP server can expose narrowly constrained security tools without granting an AI client general command authority. Contributions should preserve that central design principle.

## Before You Contribute

Please review:

- [README.md](README.md) for the project scope, architecture, and safety model
- [SECURITY.md](SECURITY.md) for private vulnerability reporting
- [Deployment Guide](docs/deployment-guide.md) for installation and validation
- [Learning Journey](docs/learning-journey.md) for the project’s design reasoning

Use this project only against systems and networks you own or are explicitly authorized to test.

## Ways to Contribute

Useful contributions include:

- Fixing documentation errors or unclear instructions
- Improving automated test coverage
- Strengthening target validation or command restrictions
- Improving structured error handling
- Improving audit reliability and integrity
- Adding safe dry-run or diagnostic behavior
- Improving dependency management
- Reproducing and documenting the Goose and Ollama integration
- Proposing narrowly scoped tools with explicit authorization rules
- Reporting bugs or security vulnerabilities responsibly

Feature requests should explain the educational value, security impact, and how the proposed behavior would remain narrowly constrained.

## Security Boundaries That Must Be Preserved

Contributions must not weaken the server-side policy boundary.

The current design requires:

- IPv4 targets to remain inside the authorized `10.10.10.0/24` lab network
- Out-of-scope, IPv6, network, and broadcast addresses to be rejected
- `scan_common_ports` to accept exactly one authorized host
- Nmap commands to be constructed entirely by the server
- User-controlled Nmap flags and command arguments to be rejected
- Nmap to be executed without invoking a shell
- The executable path, command structure, port list, and timeout to remain controlled by code
- Unexpected scan results outside the fixed allowlist to be rejected
- Security-relevant operations and authorization decisions to produce structured audit attempts
- MCP clients, models, and prompts to remain unable to modify enforced policy

Do not add:

- A general-purpose shell or command-execution tool
- Arbitrary Nmap arguments
- User-selectable scripts or executable paths
- Exploitation or credential-attack capabilities
- Persistence or destructive operations
- Automatic expansion of the authorized target scope
- Remote or unauthenticated access presented as production-ready
- Prompt-based controls as substitutes for server-side enforcement

A proposal that changes an enforced boundary must include a clear threat analysis, updated tests, and corresponding documentation.

## Reporting Security Vulnerabilities

Do not disclose suspected vulnerabilities in a public issue, discussion, pull request, or audit log.

Follow the private reporting process in [SECURITY.md](SECURITY.md).

Examples include authorization bypasses, command injection, unintended multi-host scanning, arbitrary argument injection, audit-data exposure, or another way to escape the documented tool restrictions.

## Development Setup

Clone your fork and enter the repository:

```bash
git clone https://github.com/YOUR-USERNAME/kali-mcp-security-lab.git
cd kali-mcp-security-lab
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the development dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Confirm that the required programs are available:

```bash
command -v python
command -v mcp
command -v uv
command -v nmap
```

The Python, MCP, and `uv` paths should resolve inside `.venv`. Nmap should resolve to `/usr/bin/nmap` in the documented Kali environment.

## Create a Branch

Create a focused branch from the current `main` branch:

```bash
git switch main
git pull --ff-only
git switch -c type/short-description
```

Examples:

```text
docs/improve-deployment-guide
fix/target-validation
test/add-timeout-coverage
feat/add-dry-run-mode
```

Keep each branch and pull request limited to one coherent change.

## Make the Change

When modifying code:

- Preserve the fixed authorization boundary unless the pull request explicitly proposes and justifies a policy change.
- Prefer small, readable functions with explicit inputs and outputs.
- Validate untrusted input before constructing any command.
- Use argument lists rather than shell command strings.
- Do not invoke subprocesses through a shell.
- Return structured results and structured errors.
- Avoid exposing private host information or unnecessary command output.
- Add or update tests for every changed behavior.
- Update documentation when behavior, configuration, limitations, or commands change.

Do not include unrelated formatting changes or generated files in the same pull request.

## Testing Requirements

Run the complete automated test suite:

```bash
python -m pytest -q
```

The current documented baseline is:

```text
36 passed
```

Your result may contain more tests if your contribution adds coverage. Existing tests must continue to pass.

The test suite should remain safe to run without performing live network scans. Mock operational execution where appropriate.

Depending on the change, tests should cover:

- Authorized and rejected targets
- IPv4-only enforcement
- Single-host restrictions
- Network and broadcast address rejection
- Fixed command construction
- Nmap XML parsing
- Port-allowlist validation
- Timeouts and nonzero process exits
- Malformed or unexpected output
- MCP tool discovery and invocation
- Audit success and audit-write failure behavior
- Regression cases related to the proposed change

Do not weaken, delete, or bypass a security test merely to make a change pass. If an existing expectation must change, explain why in the pull request.

## Manual Validation

Manual validation is required when a change affects MCP behavior, client integration, or live command execution.

For core MCP changes, use the procedure in the [Deployment Guide](docs/deployment-guide.md). Confirm that MCP Inspector discovers exactly the intended tools and that unauthorized requests are rejected before Nmap executes.

For Goose and Ollama changes, use [Goose and Ollama Integration](docs/goose-ollama-integration.md). Record the relevant versions, configuration, and observed results.

Manual testing must use only an isolated lab and explicitly authorized targets. Do not include private host details, operational audit logs, credentials, tokens, or sensitive environment information in the repository or pull request.

## Documentation Requirements

Documentation changes should be:

- Accurate for the current implementation
- Explicit about experimental or unsupported behavior
- Clear about which procedures have actually been validated
- Consistent across the README and files under `docs/`
- Written with copy-paste-safe commands
- Free of private infrastructure details and secrets
- Checked for broken relative links and obsolete references

Do not describe a proposed or unreproduced integration as validated. Distinguish clearly among:

- Implemented
- Covered by automated tests
- Manually validated
- Documented but pending reproduction
- Planned but not implemented

When adding or removing repository files, update the repository tree in `README.md`.

## Commit Guidelines

Use concise, descriptive commit messages. Conventional Commit-style prefixes are encouraged:

```text
docs: clarify MCP Inspector validation
fix: reject broadcast addresses as scan targets
test: add malformed XML coverage
feat: add constrained dry-run mode
refactor: simplify target parsing
chore: update development dependency constraints
```

Keep commits focused. Do not include audit logs, temporary files, local configuration, virtual environments, editor files, credentials, tokens, or private network information.

Before committing, review the staged files:

```bash
git status
git diff --staged
```

## Pull Request Checklist

Before opening a pull request, confirm:

- [ ] The change has a clear and limited purpose.
- [ ] The change preserves the documented authorization boundary.
- [ ] No arbitrary shell or Nmap authority has been introduced.
- [ ] New or changed behavior has automated test coverage.
- [ ] The complete automated test suite passes.
- [ ] Relevant manual validation has been completed when required.
- [ ] Documentation reflects the actual implementation and validation status.
- [ ] No secrets, credentials, private host information, or operational audit logs are included.
- [ ] The pull request explains security implications and known limitations.
- [ ] The diff contains no unrelated changes.

## Pull Request Description

A pull request should include:

1. **Purpose**  
   What problem does the change solve?

2. **Summary of changes**  
   Which files and behaviors changed?

3. **Security impact**  
   Does the change affect target validation, command construction, tool authority, execution, audit behavior, or data exposure?

4. **Testing performed**  
   Include the automated test result and any relevant manual validation.

5. **Documentation impact**  
   Identify the documentation updated or explain why none was required.

6. **Limitations or follow-up work**  
   Describe anything intentionally left unresolved.

For a security-boundary change, also explain:

- The threat being addressed
- The previous behavior
- The proposed enforced behavior
- Expected rejection cases
- Tests proving the boundary cannot be bypassed

## Review Expectations

Maintainers may request changes when a contribution:

- Expands authority without sufficient justification
- Relies on prompts or client behavior for enforcement
- Accepts arbitrary commands, flags, or executable paths
- Lacks tests for authorization or failure behavior
- Claims validation that has not been performed
- Introduces sensitive data into code, documentation, tests, or logs
- Mixes unrelated changes
- Moves the project toward an unsupported production deployment without the necessary security design

Approval is not guaranteed. The project may decline technically functional contributions that conflict with its educational purpose or constrained-authority model.

## Licensing

By submitting a contribution, you agree that it may be distributed under the repository’s [MIT License](LICENSE).
