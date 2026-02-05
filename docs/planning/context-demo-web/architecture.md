# Architecture: demo-web

> Technical patterns from ~/code/observability reference.
> Loaded by /cook for design context.

## Layers
- cmd/server: entry point, signal handling, server lifecycle
- internal/config: env-based configuration
- internal/db: SQLite with WAL mode, auto-migrations
- internal/models: data structures shared across layers
- internal/handlers: HTTP API + page handlers
- internal/web/templates: Templ components (.templ files)
- internal/ws: WebSocket broadcast hub

## Patterns
- net/http standard library routing (no frameworks)
- Templ for type-safe HTML generation (compiled to Go)
- Broadcast-only WebSocket hub (no client-to-server messaging)
- HTMX for interactivity (CDN, no build step)
- Tailwind CSS via CDN (no build step)
- SQLite WAL mode for concurrent reads

## Constraints
- Must work without Go framework dependencies (stdlib only for HTTP)
- SQLite only (no postgres/mysql)
- All HTML via Templ (no raw HTML strings in Go code)
- Graceful shutdown required (SIGINT/SIGTERM)

## Conventions
- Table-driven tests with t.Run()
- Config via os.Getenv with sensible defaults
- Database access only through internal/db package
- Models in internal/models, handlers never write SQL directly
