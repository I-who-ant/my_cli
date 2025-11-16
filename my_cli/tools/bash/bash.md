# Bash Tool

Execute a bash command in the shell.

## Description

This tool runs the command in a subprocess and captures stdout and stderr.
The command will be killed if it exceeds the timeout.

## Parameters

- `command` (required): The bash command to execute
- `timeout` (optional): Timeout in seconds (default: 60, max: 300)

## Examples

List files:
```bash
ls -la
```

Check disk usage:
```bash
df -h
```

Search for files:
```bash
find . -name "*.py"
```

## Notes

- Commands are executed in a non-interactive shell
- Stdout and stderr are both captured
- Long-running commands will be killed after timeout
- Output is limited to prevent context overflow
