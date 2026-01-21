# Line Cook Naming Guide

This document guides thematic naming of components in the Line Cook project, based on the established restaurant kitchen metaphor.

## The Kitchen Metaphor

**Core philosophy:** You = Chef, Line Cook = AI Assistant

Just as a line cook in a professional kitchen executes the chef's vision with skill and discipline, the Line Cook workflow system helps AI assistants execute your development tasks with structure and professionalism.

**The service cycle:**
```
prep → cook → serve → tidy
```

This mirrors a restaurant service: gather ingredients, execute orders, plate and present, clean the station. Professional discipline, structured execution.

## Naming Vocabulary

### Service Cycle Terms (Core Workflow)

| Kitchen Term | Meaning | Status |
|--------------|---------|--------|
| prep | Gather ingredients, check orders | ✓ Used |
| cook | Execute the order | ✓ Used |
| serve | Plate and present | ✓ Used |
| tidy | Clean station, close out | ✓ Used |

### Available Kitchen Terms

Terms available for future components:

| Kitchen Term | Potential Use |
|--------------|---------------|
| mise | "mise en place" - everything in its place (setup, organization) |
| ticket | An order/task to execute |
| fire | Start cooking an order (trigger execution) |
| plate | Format output for presentation |
| garnish | Final touches, polish |
| expo | Expeditor - coordinates flow between stations |
| pass | Quality check before serving |
| rush | Priority/urgent work |
| course | A phase or stage of work |
| station | A specialized work area |
| sauté | Quick, focused work |
| simmer | Background/long-running work |
| reduce | Condense, summarize |
| taste | Test, validate |
| 86 | Remove/disable (industry slang for "out of stock") |
| call | Announce status/completion |
| runner | Delivers output to destination |
| walk-in | Storage (for context, cached data) |
| pickup | Ready for collection/handoff |

## Naming Principles

1. **Single syllable preferred** - prep, cook, serve, tidy (not "preparation")
2. **Verb-based** - Commands are actions, use action words
3. **Kitchen-authentic** - Terms real chefs use, not generic cooking
4. **Progressive** - Names should suggest workflow direction
5. **Memorable** - Easy to recall during flow state

## Anti-Patterns to Avoid

- **Generic verbs:** run, execute, start, do
- **Tech jargon:** sync, deploy, compile (unless necessary)
- **Multi-word commands:** prep-station, cook-task
- **Non-kitchen metaphors:** launch, ship, queue

## Platform Naming Conventions

| Platform | Format | Example |
|----------|--------|---------|
| Claude Code | `line:verb` | `/line:prep` |
| OpenCode | `line-verb` | `/line-prep` |
| Kiro | Natural language | "prep" or "/prep" |

## Future Component Examples

When adding new features, consider these mappings:

| Feature Type | Suggested Name | Rationale |
|--------------|----------------|-----------|
| Caching | `walk-in` | Walk-in cooler = cold storage |
| Parallel execution | `stations` | Multiple work stations |
| Prioritization | `rush` or `vip` | Rush orders in kitchen |
| Final QA check | `pass` | Expo pass = final quality check |
| Cancellation | `86` | Restaurant slang for "cancel/remove" |
| Quick task | `sauté` | Fast, focused execution |
| Background work | `simmer` | Low and slow, running in background |
| Summarization | `reduce` | Reduce a sauce = concentrate/condense |
| Validation | `taste` | Chef tastes before serving |
| Handoff | `pickup` | Order ready for pickup |
