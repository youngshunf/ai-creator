---
name: ui-generator
version: "1.0.0"
description: 生成可交互的 UI 组件 (表单、卡片、按钮等)
tools: []
---

You have the ability to generate interactive UI components that will be rendered in the user's application. Use this capability when:
- The user needs to fill out a form
- You want to present data in a structured way (tables, cards)
- You need the user to make a choice or confirm an action

## UI Protocol

Output a JSON code block with the following structure:

```json
{
  "ui": {
    "type": "form",
    "id": "user_form",
    "props": { "title": "User Information" },
    "children": [
      {
        "type": "input",
        "id": "name",
        "props": { "label": "Name", "placeholder": "Enter your name" }
      },
      {
        "type": "textarea",
        "id": "bio",
        "props": { "label": "Bio", "rows": 3 }
      },
      {
        "type": "button",
        "props": { "label": "Submit" },
        "events": {
          "onClick": { "type": "onClick", "action_id": "submit_form" }
        }
      }
    ]
  },
  "expects_response": true
}
```

## Available Component Types

| Type       | Description                     | Key Props                          |
|------------|---------------------------------|------------------------------------|
| `card`     | Container with border/shadow    | `title`, `subtitle`                |
| `text`     | Plain text                      | `content`                          |
| `markdown` | Markdown-rendered text          | `content`                          |
| `heading`  | Section heading                 | `level` (1-6), `content`           |
| `form`     | Form container                  | `title`                            |
| `input`    | Text input field                | `label`, `placeholder`, `required` |
| `textarea` | Multi-line text input           | `label`, `rows`                    |
| `select`   | Dropdown select                 | `label`, `options` (list of strings) |
| `checkbox` | Checkbox input                  | `label`, `checked`                 |
| `radio`    | Radio button group              | `label`, `options`                 |
| `button`   | Clickable button                | `label`, `variant` (primary/secondary) |
| `table`    | Data table                      | `columns`, `rows`                  |
| `image`    | Image display                   | `src`, `alt`                       |
| `divider`  | Horizontal line                 | -                                  |
| `progress` | Progress bar                    | `value` (0-100), `label`           |

## Events

Use events to capture user interactions:
- `onClick`: Button clicks
- `onChange`: Input value changes
- `onSubmit`: Form submission

Event structure:
```json
"events": {
  "onClick": {
    "type": "onClick",
    "action_id": "unique_action_identifier"
  }
}
```

## Rules

1. **Always wrap in JSON code block**: Use ```json ... ``` syntax.
2. **Set `expects_response: true`** if you need to wait for user interaction (e.g., form submission).
3. **Use unique `id` values** for form fields to receive data correctly.
4. **Keep UI simple**: Don't overwhelm the user with too many fields.
5. **Prefer UI over plain text** when structured input/output is beneficial.

## Example: Confirmation Dialog

```json
{
  "ui": {
    "type": "card",
    "props": { "title": "Confirm Action" },
    "children": [
      { "type": "text", "props": { "content": "Are you sure you want to proceed?" } },
      {
        "type": "row",
        "children": [
          {
            "type": "button",
            "props": { "label": "Cancel", "variant": "secondary" },
            "events": { "onClick": { "type": "onClick", "action_id": "cancel" } }
          },
          {
            "type": "button",
            "props": { "label": "Confirm", "variant": "primary" },
            "events": { "onClick": { "type": "onClick", "action_id": "confirm" } }
          }
        ]
      }
    ]
  },
  "expects_response": true
}
```
