# WebSearch Tool

Search the web using DuckDuckGo search engine.

## When to Use

- **Finding information**: Search for facts, documentation, tutorials, or answers
- **Researching topics**: Gather information about a specific subject
- **Looking up latest news**: Find recent articles or updates
- **Finding code examples**: Search for programming solutions and examples
- **Verifying facts**: Cross-check information from web sources

## Parameters

- `query` (required): The search query text
- `limit` (optional): Number of results to return (default: 5, max: 10)

## Examples

**Example 1: General search**
```
WebSearch(query="Python asyncio tutorial", limit=5)
```

**Example 2: Technical documentation**
```
WebSearch(query="React hooks useEffect documentation", limit=3)
```

**Example 3: Latest news**
```
WebSearch(query="AI developments 2024", limit=5)
```

## Guidelines

- **Be specific**: Use clear and specific search terms
- **Use keywords**: Focus on important keywords rather than full sentences
- **Adjust limit**: Use smaller limits (3-5) for focused searches
- **Refine queries**: If results aren't helpful, try different keywords

## Important Notes

- This tool uses DuckDuckGo search (no API key required)
- Results include title, URL, and snippet for each page
- Does not include full page content (use WebFetch for that)
- Respects search engine rate limits
