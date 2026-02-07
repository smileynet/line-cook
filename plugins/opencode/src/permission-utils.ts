/**
 * Permission utilities for auto-approval of safe operations.
 *
 * This module provides functions to determine if a permission request
 * should be auto-approved, denied, or require manual user approval.
 */
import type { Permission } from "@opencode-ai/sdk"

/**
 * Safe read-only bash commands that can be auto-approved.
 * These commands don't modify the filesystem or system state.
 */
export const SAFE_BASH_PATTERNS: RegExp[] = [
  // File reading (read-only)
  /^cat\s+/i,
  /^head\s+/i,
  /^tail\s+/i,
  /^less\s+/i,
  /^more\s+/i,
  /^file\s+/i,
  /^wc\s+/i,
  /^stat\s+/i,

  // Directory listing
  /^ls(\s|$)/i,
  /^dir(\s|$)/i,
  /^tree(\s|$)/i,
  /^pwd(\s|$)/i,

  // Search and find (read-only)
  /^grep\s+/i,
  /^rg\s+/i, // ripgrep
  /^find\s+.*-type\s+[fd]/i, // find with type filter (no -exec or -delete)
  /^find\s+.*-name\s+/i, // find by name
  /^which\s+/i,
  /^whereis\s+/i,
  /^locate\s+/i,
  /^fd\s+/i, // fd-find

  // Git read-only operations
  /^git\s+status(\s|$)/i,
  /^git\s+log(\s|$)/i,
  /^git\s+diff(\s|$)/i,
  /^git\s+show(\s|$)/i,
  /^git\s+branch(\s|$)/i,
  /^git\s+remote\s+-v(\s|$)/i,
  /^git\s+tag(\s|$)/i,
  /^git\s+describe(\s|$)/i,
  /^git\s+rev-parse(\s|$)/i,
  /^git\s+ls-files(\s|$)/i,
  /^git\s+blame(\s|$)/i,

  // Beads read-only commands
  /^bd\s+list(\s|$)/i,
  /^bd\s+show(\s|$)/i,
  /^bd\s+ready(\s|$)/i,
  /^bd\s+blocked(\s|$)/i,
  /^bd\s+stats(\s|$)/i,
  /^bd\s+search(\s|$)/i,
  /^bd\s+sync\s+--status(\s|$)/i,
  /^bd\s+doctor(\s|$)/i,

  // System info (read-only)
  /^date(\s|$)/i,
  /^whoami(\s|$)/i,
  /^hostname(\s|$)/i,
  /^uname(\s|$)/i,
  /^env(\s|$)/i,
  /^printenv(\s|$)/i,
  /^echo\s+\$/i, // echo $VAR (reading env vars)

  // Package manager queries (read-only)
  /^npm\s+list(\s|$)/i,
  /^npm\s+ls(\s|$)/i,
  /^npm\s+view(\s|$)/i,
  /^npm\s+info(\s|$)/i,
  /^npm\s+outdated(\s|$)/i,
  /^bun\s+pm\s+ls(\s|$)/i,
  /^pip\s+list(\s|$)/i,
  /^pip\s+show(\s|$)/i,
  /^cargo\s+tree(\s|$)/i,
  /^go\s+list(\s|$)/i,
]

/**
 * Commands that look safe but could be destructive with certain flags.
 * These patterns DENY auto-approval when matched.
 */
export const SAFE_BASH_EXCLUSIONS: RegExp[] = [
  // find with -exec or -delete is destructive
  /^find\s+.*-exec/i,
  /^find\s+.*-delete/i,
  /^find\s+.*-ok/i,

  // Piping to destructive commands
  /\|\s*rm\s/i,
  /\|\s*xargs\s+rm/i,
  /\|\s*tee\s/i, // tee writes files

  // Output redirection is not read-only
  /\s>\s/,
  /\s>>\s/,
]

/**
 * Safe tool types that can be auto-approved.
 * These are OpenCode tools that only read data.
 */
export const SAFE_TOOL_TYPES = new Set([
  "read",
  "glob",
  "grep",
  "list",
  "search",
])

/**
 * Dangerous command patterns that should be blocked entirely.
 * These patterns match destructive operations that should never be run automatically.
 */
export const DANGEROUS_PATTERNS: RegExp[] = [
  /git\s+push.*--force/i,
  /git\s+reset.*--hard/i,
  /rm\s+-rf\s+\/\s*$/i, // rm -rf / (root, end of command)
  /rm\s+-rf\s+\/\*/i, // rm -rf /* (root wildcard)
  /rm\s+-rf\s+\/[a-z]/i, // rm -rf /home, /etc, etc. (root subdirs)
  /rm\s+-rf\s+~/i, // rm -rf ~ (home)
  /rm\s+-rf\s+\$HOME/i, // rm -rf $HOME
  /rm\s+-rf\s+%USERPROFILE%/i, // Windows home
  /rmdir\s+\/s\s+\/q\s+C:\\/i, // Windows root delete
  /del\s+\/f\s+\/s\s+\/q\s+C:\\/i, // Windows recursive delete
  /format\s+[A-Z]:/i, // Windows format drive
  /:\(\)\{\s*:\|:&\s*\};:/, // Fork bomb
  />\s*\/dev\/sda/, // Write to disk device
  /dd\s+if=.*of=\/dev\/sd/i, // dd to disk
  /mkfs\./i, // Format filesystem
]

/**
 * Check if a command matches any dangerous pattern.
 */
export function isDangerousCommand(command: string): { dangerous: boolean; pattern?: string } {
  for (const pattern of DANGEROUS_PATTERNS) {
    if (pattern.test(command)) {
      return { dangerous: true, pattern: pattern.source }
    }
  }
  return { dangerous: false }
}

/**
 * Check if a bash command is safe (read-only) for auto-approval.
 * Returns true if the command matches a safe pattern and doesn't match any exclusion.
 */
export function isSafeBashCommand(command: string): boolean {
  // Trim and normalize the command
  const trimmed = command.trim()

  // Check exclusions first (deny patterns)
  for (const exclusion of SAFE_BASH_EXCLUSIONS) {
    if (exclusion.test(trimmed)) {
      return false
    }
  }

  // Check if it matches any safe pattern
  for (const pattern of SAFE_BASH_PATTERNS) {
    if (pattern.test(trimmed)) {
      return true
    }
  }

  return false
}

/**
 * Determine if a permission request should be auto-approved.
 * Returns "allow" to auto-approve, "ask" to prompt user, or "deny" to block.
 */
export function shouldAutoApprove(permission: Permission): "allow" | "ask" | "deny" {
  const { type, pattern, metadata } = permission

  // Check tool type-based permissions
  const toolType = type.toLowerCase()

  // Auto-approve safe tool types
  if (SAFE_TOOL_TYPES.has(toolType)) {
    return "allow"
  }

  // For bash/shell permissions, check the command
  if (toolType === "bash" || toolType === "shell") {
    // Get command from pattern or metadata
    const command =
      (typeof pattern === "string" ? pattern : pattern?.[0]) ||
      (metadata?.command as string) ||
      (metadata?.cmd as string) ||
      ""

    if (!command) {
      return "ask" // No command to analyze, ask user
    }

    // First check if it's dangerous (should be denied)
    const { dangerous } = isDangerousCommand(command)
    if (dangerous) {
      return "deny"
    }

    // Then check if it's safe (can be auto-approved)
    if (isSafeBashCommand(command)) {
      return "allow"
    }
  }

  // Default: ask the user
  return "ask"
}
