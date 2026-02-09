# TodoWebApp Brainstorm

## Problem Statement
Build a minimal viable todo web application demonstrating core functionality.

## User Needs
- Users need to track tasks they need to do
- Users need to mark tasks as complete
- Users need their data to persist across sessions

## Ideas

### Core Features
1. **Add Todo** — Input field + button to create new items
2. **Toggle Complete** — Click to mark done/undone with visual feedback
3. **Persist State** — Use localStorage so data survives page reload

### Nice-to-Haves (Parking Lot)
- Delete individual todos
- Filter by status (all/active/completed)
- Clear all completed
- Due dates
- Cloud sync

## Technical Approach
- Vanilla JS, no frameworks
- Single-page HTML with embedded styles
- localStorage as JSON for persistence
- Simple test framework (no Jest dependency)

## Constraints
- Must work offline (no server required)
- Must work in modern browsers (ES6+)
- No build step required

## Open Questions
- How to generate unique IDs? → `Date.now().toString(36)`
- How to structure tests? → Simple assert helper in test file
