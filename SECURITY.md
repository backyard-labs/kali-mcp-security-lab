# Security Policy

## Project Status

Kali MCP Security Lab is an experimental educational project. It is not production-ready and should be used only in an isolated lab against systems you own or are explicitly authorized to test.

## Supported Versions

This project does not currently publish stable production releases.

| Version | Supported |
|---|---|
| Latest commit on `main` | Best-effort security fixes |
| Older commits, forks, and modified versions | Not supported |

Security fixes are applied only to the current `main` branch. No response or remediation service-level agreement is provided.

## Reporting a Vulnerability

Do not report suspected vulnerabilities through a public GitHub issue, discussion, pull request, or audit log.

Use GitHub Private Vulnerability Reporting:

[Report a vulnerability privately](https://github.com/backyard-labs/kali-mcp-security-lab/security/advisories/new)

Include:

- A clear description of the vulnerability
- The affected commit or version
- The relevant MCP tool or component
- Reproduction steps or a minimal proof of concept
- The expected and observed behavior
- The potential security impact
- Suggested remediation, if known

Remove API keys, credentials, personal information, private host information, operational audit records, and data from systems you do not own.

If private vulnerability reporting is unavailable, do not publish technical details. Open a minimal issue stating that you need a private security-reporting channel, without describing the vulnerability.

## Security Scope

Examples of issues considered security-sensitive include:

- Bypassing the authorized `10.10.10.0/24` network restriction
- Causing a single-host tool to scan multiple hosts or a subnet
- Scanning network, broadcast, IPv6, or out-of-scope addresses
- Injecting arbitrary Nmap arguments or shell commands
- Executing a program other than the fixed authorized Nmap command
- Expanding the fixed common-port allowlist without a code change
- Bypassing server-side validation through malformed MCP input
- Exposing sensitive information through MCP responses or audit records
- Tampering with authorization decisions or security-relevant audit data
- Dependency vulnerabilities that are exploitable through this project

The following are generally not treated as vulnerabilities in this repository:

- The documented ability to scan explicitly authorized lab targets
- Model hallucinations or incorrect conversational responses that do not bypass server-side enforcement
- Goose selecting the wrong tool when the server still enforces its policy
- Missing audit events caused by the documented best-effort, fail-open audit limitation
- Unsupported production, remote, multi-user, or internet-facing deployment
- Vulnerabilities that exist only in a modified fork
- General feature requests or documentation corrections
- Vulnerabilities solely in upstream projects with no demonstrated impact on this repository

Upstream vulnerabilities should also be reported to the affected upstream project.

## Coordinated Disclosure

Please allow reasonable time to investigate and address a confirmed vulnerability before publishing technical details.

The maintainer will handle reports on a best-effort basis and may:

1. Confirm receipt.
2. Request additional reproduction information.
3. Assess severity and affected components.
4. Develop and test a correction.
5. Publish a security advisory when appropriate.

Do not perform testing against systems, networks, or accounts without explicit authorization.

## Security Design Limitations

The current implementation has known limitations:

- It is an educational lab project, not a hardened production service.
- MCP communication uses local `stdio` transport.
- The server does not independently authenticate MCP clients.
- The authorized subnet is fixed in code.
- Audit logging is best-effort and fails open.
- Remote and multi-user deployment are outside the supported scope.
- The Goose and Ollama integration is documented but remains pending independent reproduction and recorded validation.

These documented limitations may still justify a private report if they can be used to bypass an enforced security boundary beyond the behavior already described.
