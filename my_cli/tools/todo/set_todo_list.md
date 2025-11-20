# SetTodoList Tool

Update the todo list to track tasks and their status.

## When to Use

- **Planning work**: Breaking down complex tasks into smaller steps
- **Tracking progress**: Monitoring what's done and what's pending
- **Organizing tasks**: Prioritizing and managing multiple tasks
- **Showing status**: Communicating current progress to the user

## Parameters

- `todos` (required): List of todo items, each with:
  - `title` (string): Description of the task
  - `status` (string): One of "Pending", "In Progress", or "Done"

## Examples

**Example 1: Initial task breakdown**
```
SetTodoList(todos=[
    {"title": "Read project requirements", "status": "Done"},
    {"title": "Design database schema", "status": "In Progress"},
    {"title": "Implement API endpoints", "status": "Pending"},
    {"title": "Write tests", "status": "Pending"}
])
```

**Example 2: Progress update**
```
SetTodoList(todos=[
    {"title": "Read project requirements", "status": "Done"},
    {"title": "Design database schema", "status": "Done"},
    {"title": "Implement API endpoints", "status": "In Progress"},
    {"title": "Write tests", "status": "Pending"}
])
```

## Guidelines

- **Be specific**: Use clear, actionable task titles
- **Update regularly**: Reflect actual progress
- **Keep it current**: Remove completed tasks or mark as Done
- **Break down tasks**: Split large tasks into smaller, manageable steps
- **Show progress**: Move tasks from Pending → In Progress → Done

## Status Meanings

- **Pending**: Task not yet started
- **In Progress**: Currently working on this task
- **Done**: Task completed

## Important Notes

- This tool replaces the entire todo list (not append)
- Use it to show the user what you're working on
- Helps maintain transparency about your progress
- Useful for multi-step tasks and complex implementations
