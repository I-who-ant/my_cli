# ReadFile Tool

Read the contents of a file.

## Description

This tool reads the entire file content and returns it as a string.
The file must exist and be readable.

## Parameters

- `path` (required): The path to the file to read

## Examples

Read a Python file:
```
path: src/main.py
```

Read a configuration file:
```
path: config.json
```

## Notes

- File must exist and be readable
- Content is read as UTF-8 text
- Binary files may not be read correctly
- Large files are automatically truncated to prevent context overflow
