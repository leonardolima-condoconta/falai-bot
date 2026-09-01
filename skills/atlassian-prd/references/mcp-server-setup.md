# MCP Server Setup
```json
{"mcpServers":{"atlassian":{"command":"uvx","args":["mcp-atlassian"],"env":{"JIRA_URL":"https://domain.atlassian.net","JIRA_USERNAME":"user@example.com","JIRA_API_TOKEN":"${JIRA_API_TOKEN}","CONFLUENCE_URL":"https://domain.atlassian.net/wiki","CONFLUENCE_USERNAME":"user@example.com","CONFLUENCE_API_TOKEN":"${CONFLUENCE_API_TOKEN}"}}}}
```
Ferramentas: createJiraIssue, editJiraIssue, transitionJiraIssue, searchJiraIssuesUsingJql, createConfluencePage, updateConfluencePage, searchConfluenceUsingCql