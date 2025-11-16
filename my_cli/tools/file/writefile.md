# WriteFile Tool

Write content to a file.

## Description

This tool writes the given content to the specified file.
If the file exists, it will be overwritten.
Parent directories will be created if they don't exist.

## Parameters

- `path` (required): The path to the file to write
- `content` (required): The content to write to the file

## Examples

Create a Python file:
```
path: src/hello.py
content: print("Hello, World!")
```

Create a configuration file:
```
path: config.json
content: {"version": "1.0"}
```

## Notes

- Parent directories are created automatically
- Existing files are overwritten
- Content is written as UTF-8 text
- File permissions are set to default (0644)
