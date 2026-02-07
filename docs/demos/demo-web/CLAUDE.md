# Line Cook Dashboard

Go web dashboard for monitoring Line Cook workflows in real time.

## Stack
- Go 1.25+, Templ (HTML templating), SQLite (WAL mode)
- HTMX for interactivity, Tailwind CSS (CDN) for styling
- Gorilla WebSocket for live updates

## Structure
cmd/server/main.go           - Entry point, HTTP server, signal handling
internal/config/config.go    - Environment-based configuration
internal/db/db.go            - SQLite wrapper, migrations
internal/db/queries.go       - Query functions
internal/models/models.go    - Data structures (LoopStatus, Iteration, HookEvent)
internal/handlers/api.go     - API handlers (POST /events, GET /events/recent)
internal/handlers/pages.go   - Page handlers (GET /, GET /history)
internal/web/templates/      - Templ components (.templ files)
internal/ws/hub.go           - WebSocket hub, broadcast-only

## Data Sources
1. Loop files: reads status.json + history.jsonl from configurable directory
2. Hook events: POST /events endpoint receives Claude Code hook payloads

## Commands
go test ./...                        # Run tests
go build -o server ./cmd/server      # Build
./server                             # Run (default :4000)
templ generate                       # Regenerate Templ output

## Environment Variables
PORT=4000          - HTTP server port
DB_PATH=dashboard.db - SQLite database path
LOOP_DATA_DIR=     - Path to loop data directory (e.g. /tmp/line-loop-myproject)

## Conventions
- net/http standard library for routing (no frameworks)
- Templ for all HTML generation (no raw HTML strings in Go)
- All database access through internal/db package
- Models in internal/models, handlers call db, never direct SQL
- Tests use table-driven patterns with t.Run()
- Graceful shutdown on SIGINT/SIGTERM (30s timeout)
