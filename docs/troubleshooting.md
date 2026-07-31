# Troubleshooting MCP Inspector

## Symptom

MCP Inspector opens, but its status remains **Connecting...** and the control is disabled.

## Check the Active Environment

```bash
command -v python
command -v mcp
command -v uv
```

These commands show which executables the shell will use. The Python, MCP, and `uv` paths should all point into the project's `.venv` directory.

## Check for Leftover Processes

```bash
ps -ef | grep -E '[m]cp-inspector|[k]ali_lab_server|[i]nspector.*6274'
ss -ltnp | grep -E '6274|6277'
```

`ps` identifies Inspector and server processes. `ss` shows whether an expected local TCP port is listening. The bracketed patterns prevent `grep` from matching its own command line.

Stop any known stale instance before starting another. Avoid terminating unrelated processes.

## Start One Logged Instance

```bash
mcp dev kali_lab_server.py 2>&1 | tee mcp-inspector.log
```

`2>&1` combines standard error with standard output. `tee` displays the output while saving a copy for later review.

In a second activated terminal, inspect the current state:

```bash
ss -ltnp | grep -E '6274|6277'
tail -n 100 mcp-inspector.log
```

The first command confirms the listener. The second shows the most recent Inspector messages.

## Confirm the Complete URL

Open the exact tokenized localhost URL printed by Inspector. Opening only `http://localhost:6274` can omit the temporary authentication value.

Do not publish or share the token. Stop Inspector with `Ctrl+C` when finished; a new launch generates a new token.

## Browser-Specific Failure Seen in This Lab

In Firefox:

- The page assets loaded.
- The Python MCP process was alive.
- Inspector listened on localhost.
- No Python or Inspector rejection appeared.
- Firefox's Network panel showed `events` requests aborted with `NS_BINDING_ABORTED`.

Opening the same complete URL in Chromium succeeded. MCP initialization and tool listing then completed normally.

The practical workaround is to use Chromium for Inspector. The deeper lesson is to verify the backend, transport, and browser independently before changing server code or reinstalling dependencies.
