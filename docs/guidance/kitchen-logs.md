# Kitchen Logs

> Track what happens during service for debugging and improvement.

Effective logging helps diagnose issues, understand behavior, and improve over time. Like a chef's mise en place log or a kitchen's order history, logs tell the story of what happened.

## Quick Reference

| Level | When to Use | Examples |
|-------|-------------|----------|
| **ERROR** | Something failed | "Failed to connect to database" |
| **WARN** | Unexpected but handled | "Retrying request, attempt 2/3" |
| **INFO** | Significant events | "Server started on :8080" |
| **DEBUG** | Development details | "Parsed config: {timeout: 30s}" |

## The Kitchen Analogy

During service, a kitchen tracks:

1. **Orders in** - When orders arrive, what was ordered
2. **Station updates** - "Order 42 at grill"
3. **Completions** - "Order 42 up"
4. **Issues** - "86'd the salmon" (out of stock)

Software logging follows the same pattern.

## Log Levels

### ERROR

Something failed and needs attention:

```go
log.Error("database connection failed",
    "error", err,
    "host", config.DBHost,
    "retries", 3)
```

When to use:
- Unrecoverable errors
- Failed operations
- Things that need fixing

### WARN

Something unexpected that was handled:

```go
log.Warn("slow query detected",
    "query", queryName,
    "duration", duration,
    "threshold", slowQueryThreshold)
```

When to use:
- Retries that succeeded
- Fallback paths taken
- Near-limit conditions

### INFO

Normal significant events:

```go
log.Info("server started",
    "address", addr,
    "version", version)

log.Info("request completed",
    "method", req.Method,
    "path", req.URL.Path,
    "status", statusCode,
    "duration", duration)
```

When to use:
- Startup/shutdown
- Configuration loaded
- Important state changes
- Request summaries

### DEBUG

Details for development:

```go
log.Debug("parsing configuration",
    "file", configPath,
    "contents", string(data))

log.Debug("cache lookup",
    "key", key,
    "hit", found)
```

When to use:
- Internal state
- Algorithm details
- Cache behavior
- Verbose tracing

## Structured Logging

Always use structured logging with key-value pairs:

```go
// Good: Structured with context
log.Error("failed to process order",
    "order_id", orderID,
    "customer", customerID,
    "error", err)

// Bad: String concatenation
log.Error("failed to process order " + orderID + ": " + err.Error())
```

Benefits:
- Searchable in log aggregators
- Consistent format
- Easy to parse programmatically
- No format string vulnerabilities

## Context Propagation

Include request/trace context in all logs:

```go
func handleRequest(ctx context.Context, req *Request) {
    logger := log.With(
        "request_id", req.ID,
        "user_id", req.UserID,
        "trace_id", trace.FromContext(ctx),
    )

    logger.Info("processing request")

    // All subsequent logs include context
    if err := process(ctx, req); err != nil {
        logger.Error("processing failed", "error", err)
        return
    }

    logger.Info("request completed")
}
```

## What to Log

### Always Log

- **Startup/shutdown:** Configuration, versions, addresses
- **Errors:** All errors with context
- **Authentication:** Login attempts (success/failure)
- **Authorization:** Access denied events
- **State changes:** Important transitions
- **External calls:** Requests to other services

### Never Log

- **Secrets:** Passwords, tokens, keys
- **PII:** Without proper redaction
- **High-volume data:** Every loop iteration
- **Binary data:** Large blobs, images

### Log Carefully

- **Request/response bodies:** May contain sensitive data
- **User input:** May contain PII
- **Database queries:** May expose schema/data

## Redaction

Redact sensitive data before logging:

```go
type RedactedToken string

func (t RedactedToken) String() string {
    if len(t) > 8 {
        return string(t[:4]) + "****" + string(t[len(t)-4:])
    }
    return "****"
}

log.Info("token validated",
    "token", RedactedToken(token),  // logs: "eyJh****dXJ9"
    "user_id", userID)
```

## Performance Considerations

### Lazy Evaluation

For expensive operations, check level first:

```go
// Good: Only compute if debug enabled
if log.IsDebugEnabled() {
    log.Debug("request details",
        "body", expensiveSerialize(body))
}

// Or use lazy values
log.Debug("request details",
    "body", slog.Any("body", &lazyBody{body}))
```

### Sampling

For high-volume events, sample instead of logging all:

```go
if requestCount%100 == 0 {
    log.Info("request sample",
        "count", requestCount,
        "sample_rate", "1%")
}
```

## Log Anti-patterns

### Log and Throw

> Log the error, then return it for caller to log again.

```go
// Bad: Logs same error multiple times
func doThing() error {
    err := subThing()
    if err != nil {
        log.Error("subThing failed", "error", err)
        return err  // Caller will also log
    }
}

// Good: Log at the top, or wrap context
func doThing() error {
    err := subThing()
    if err != nil {
        return fmt.Errorf("doThing: %w", err)  // Wrap, don't log
    }
}
```

### Missing Context

> "Error occurred" with no details.

```go
// Bad: No context
log.Error("error occurred")

// Good: Full context
log.Error("failed to save user",
    "user_id", userID,
    "error", err,
    "operation", "update")
```

### Logging in Loops

> Logging every iteration of a large loop.

```go
// Bad: 10000 log lines
for _, item := range items {
    log.Debug("processing item", "item", item)
}

// Good: Summary logging
log.Debug("processing items", "count", len(items))
for _, item := range items {
    // process
}
log.Debug("items processed", "success", successCount, "failed", failedCount)
```

### Inconsistent Levels

> Using INFO for errors or DEBUG for critical events.

```go
// Bad: Wrong level
log.Info("database connection failed", "error", err)  // Should be ERROR

// Good: Appropriate level
log.Error("database connection failed", "error", err)
```

## Debugging Workflow

When debugging an issue:

1. **Check error logs:** Start with ERROR level
2. **Add context:** Enable DEBUG for the relevant component
3. **Trace the request:** Follow request_id through logs
4. **Look for patterns:** Similar errors, timing correlations
5. **Check metrics:** Cross-reference with monitoring

## Log Configuration

Configure logging per environment:

```yaml
# Development
logging:
  level: debug
  format: text  # Human-readable
  output: stdout

# Production
logging:
  level: info
  format: json  # Machine-parseable
  output: stdout  # Let orchestrator collect
```

## Related

- [Workflow](./workflow.md) - Where logging fits in development
- [Station Management](./station-management.md) - Session and context tracking
- [Test Prep](./test-prep.md) - Testing log output
