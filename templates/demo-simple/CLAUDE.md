# TodoWebApp

Vanilla JS todo app for Line Cook demo.

## Stack

- ES6+ JavaScript, no frameworks
- localStorage for persistence
- No build tools

## Structure

```
index.html      - UI with form and list
src/todo.js     - TodoApp class
src/todo.test.js - Tests (run: node src/todo.test.js)
```

## Conventions

- Simple test framework (no Jest/Mocha)
- Each todo: `{id, text, completed, createdAt}`
- IDs generated with `Date.now().toString(36)`

## Test Command

```bash
node src/todo.test.js
```

## Build

No build step required. Open `index.html` in browser.
