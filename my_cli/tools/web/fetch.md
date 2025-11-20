# WebFetch Tool

Fetch and extract content from a web page URL.

## When to Use

- **Reading articles**: Extract text content from web pages
- **Fetching documentation**: Get documentation pages as text
- **Analyzing web content**: Extract main content from HTML
- **Following up searches**: Get full content after searching

## Parameters

- `url` (required): The URL to fetch content from

## Examples

**Example 1: Fetch article**
```
WebFetch(url="https://example.com/article")
```

**Example 2: Get documentation**
```
WebFetch(url="https://docs.python.org/3/library/asyncio.html")
```

## Guidelines

- **Use after search**: First search with WebSearch, then fetch specific URLs
- **Check accessibility**: Some pages may require authentication or JavaScript
- **Respect limits**: Don't fetch too many pages in quick succession
- **Verify URLs**: Ensure the URL is accessible and valid

## Important Notes

- This tool extracts main text content from HTML pages
- Uses trafilatura library for content extraction
- Automatically handles different content types (HTML, plain text, markdown)
- May not work with JavaScript-heavy pages that require rendering
- Respects standard HTTP headers and follows redirects
