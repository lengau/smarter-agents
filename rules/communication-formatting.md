---
applyTo: '**'
description: 'Agent communication standards, artifact generation, and rich markdown formatting.'
---

# Rule: Communication & UI Formatting Standards

## 1. Rich Artifact Generation

Do not clutter the chat history with extensive reports, long code diffs, or persistent information (like task lists or
logs).

- **Use Artifacts**: Generate persistent Markdown "Artifacts" for tables, diagrams, formatted data, or architecture
  specs.
- **No Redundant Summaries**: After creating or updating an artifact, do not re-summarize its entire contents in the
  chat response. Highlight only key open questions or decisions that require user input.

## 2. Navigation & Referencing

- **Mandatory Symbol Linking**: Always create clickable links for files and code symbols (classes, types, functions)
  using the file scheme. Use GitHub-style markdown links (e.g., `[filename](file:///absolute/path/to/file)`).
- **Line Ranges**: Link to specific line ranges where applicable (e.g.,
  `[file.py:L10-20](file:///path/to/file#L10-L20)`).

## 3. Advanced Markdown Components

Utilize advanced Markdown extensions to structure information effectively:

- **Alerts**: Use GitHub-style alerts (`> [!NOTE]`, `> [!WARNING]`, `> [!IMPORTANT]`) strategically for emphasis.
- **Mermaid Diagrams**: Create Mermaid diagrams inside ````mermaid```` blocks to visualize complex architectures,
  workflows, or relationships.
- **Carousels**: When presenting multiple related snippets, alternative approaches, or UI progressions, group them using
  Markdown carousels if supported by the UI.

## 4. Concise Delivery

- Provide straight-to-the-point answers free of conversational filler.
- Format responses cleanly and assume a highly technical user.
- **Ask for Clarification**: If unsure about the user's intent, explicitly ask for clarification rather than making
  broad assumptions that lead to scope creep.
