## Purpose

<!--
What problem does this pull request solve?
Keep the change focused on one coherent purpose.

Do not disclose suspected vulnerabilities or sensitive security details in this pull request.
Follow SECURITY.md and use GitHub Private Vulnerability Reporting instead.
-->

## Related Issue

<!-- Link the related issue using "Closes #123", "Fixes #123", or write "None". -->

Closes #

## Summary of Changes

<!-- Identify the files, components, and behaviors changed. -->

-
-
-

## Change Type

<!-- Select every type that applies. -->

- [ ] Documentation
- [ ] Bug fix
- [ ] Automated tests
- [ ] Security-boundary improvement
- [ ] Narrowly constrained feature
- [ ] Refactoring with no intended behavior change
- [ ] Dependency or development-workflow change
- [ ] Breaking change

## Security Impact

<!--
Explain whether this change affects target validation, command construction,
executable selection, tool authority, subprocess execution, result parsing,
audit behavior, data exposure, or another security boundary.

Write "No security-boundary impact" only when appropriate.
-->

### Authority changes

<!--
Does this change expand, reduce, or otherwise modify what an MCP client can
request or what the server can execute?

If authority changes, explain why the change is necessary and how the resulting
authority remains narrowly constrained. Otherwise, write "None".
-->

### Threats and abuse cases considered

<!--
Describe relevant bypass attempts, malformed inputs, unauthorized targets,
command-injection risks, multi-host behavior, sensitive-data exposure,
audit failure, or other failure modes.

Write "Not applicable" only when the change cannot affect a security boundary.
-->

## Enforced Behavior

<!--
Complete this section when changing an enforced security boundary or tool
behavior. Otherwise, write "Not applicable".
-->

- Accepted inputs:
- Rejected inputs:
- Server-controlled values:
- Expected failure behavior:
- Audit behavior:

## Testing Performed

### Automated tests

<!-- Paste the actual command and result. Do not include secrets or private environment information. -->

```text
python -m pytest -q
Result:
```

<!-- Identify new or modified tests. Write "None" if no tests changed and explain why. -->

-
-

### Manual validation

<!--
Describe relevant MCP Inspector, Goose/Ollama, or operational validation.

If manual validation was unnecessary or not performed, state that explicitly
and explain why. Do not include credentials, private host details, operational
audit records, or sensitive command output.
-->

### Failure and rejection cases tested

<!--
List the invalid, unauthorized, malformed, timeout, or error cases verified.
Write "Not applicable" only when the change cannot affect these behaviors.
-->

-
-

## Documentation Impact

<!-- Select every item that applies. -->

- [ ] README updated
- [ ] Deployment or integration documentation updated
- [ ] Security or contribution documentation updated
- [ ] Repository tree updated because files were added or removed
- [ ] Code comments or docstrings updated
- [ ] No documentation change was required

### Explanation

<!-- Identify the documentation changed or explain why no update was required. -->

## Validation Status

<!--
Select every status that accurately applies.
Do not describe unreproduced behavior as validated.
-->

- [ ] Implemented
- [ ] Covered by automated tests
- [ ] Manually validated
- [ ] Documented but pending reproduction
- [ ] Planned or proposed but not implemented

## Compatibility and Dependencies

<!--
Describe changes to Python, MCP, Nmap, operating-system, client, configuration,
or dependency requirements. Identify any migration steps or breaking behavior.
Write "No compatibility or dependency impact" when appropriate.
-->

## Limitations and Follow-up Work

<!-- Describe known limitations, deferred work, unresolved questions, or write "None". -->

## Contributor Checklist

<!-- Complete every applicable item before requesting review. -->

- [ ] The change has a clear and limited purpose.
- [ ] I searched for related issues and pull requests.
- [ ] I reviewed `CONTRIBUTING.md`, `SECURITY.md`, and `CODE_OF_CONDUCT.md`.
- [ ] The change preserves the documented authorization boundary, or any boundary change is explicitly justified above.
- [ ] No general shell, arbitrary command, arbitrary Nmap argument, or user-selected executable authority was introduced.
- [ ] Untrusted input is validated server-side before command construction or execution.
- [ ] Subprocess execution does not invoke a shell.
- [ ] New or changed behavior has appropriate automated test coverage.
- [ ] Relevant rejection and failure cases are tested.
- [ ] The complete automated test suite passes.
- [ ] Relevant manual validation was completed when required.
- [ ] Documentation matches the actual implementation and validation status.
- [ ] New, renamed, or removed files are reflected in the README repository tree.
- [ ] Dependency or compatibility changes are documented.
- [ ] No secrets, credentials, personal information, private host details, sensitive command output, or operational audit records are included.
- [ ] The diff contains no unrelated changes.
- [ ] Any security-sensitive information was reported privately rather than included in this pull request.

## Reviewer Notes

<!--
Call attention to the highest-risk changes, important design decisions, or
specific files and behaviors reviewers should examine closely.
-->
