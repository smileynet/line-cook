/**
 * TUI Control Utilities for Line Cook
 *
 * Wraps OpenCode TUI HTTP endpoints for hybrid automation including:
 * - appendPrompt() - Pre-fill prompts in the TUI
 * - submitPrompt() - Trigger prompt execution
 * - executeCommand() - Run slash commands externally
 * - showToast() - Display notifications
 *
 * Useful for IDE integrations, CI workflows, and external automation.
 *
 * @module tui-control
 */

import { createClient, ClientOptions } from "./sdk-integration"

/**
 * Toast notification variants
 */
export type ToastVariant = "success" | "error" | "info" | "warning"

/**
 * Options for showing a toast notification
 */
export interface ToastOptions {
  /** Toast title (optional) */
  title?: string
  /** Toast message (required) */
  message: string
  /** Toast variant/style */
  variant?: ToastVariant
  /** Duration in milliseconds (default: 5000) */
  duration?: number
}

/**
 * Result from TUI operations
 */
export interface TuiOperationResult {
  /** Whether the operation succeeded */
  success: boolean
  /** Error message if operation failed */
  error?: string
}

/**
 * Append text to the current prompt in the TUI
 *
 * Pre-fills the prompt input with text without executing it.
 * Useful for suggesting prompts that the user can review and modify.
 *
 * @param text - Text to append to the prompt
 * @param clientOptions - Client configuration
 * @returns Operation result
 *
 * @example
 * ```typescript
 * // Pre-fill a prompt for the user to review
 * await appendPrompt("Run the test suite with coverage")
 *
 * // The user can then modify and submit the prompt
 * ```
 */
export async function appendPrompt(
  text: string,
  clientOptions: ClientOptions = {}
): Promise<TuiOperationResult> {
  if (!text || !text.trim()) {
    return { success: false, error: "Text cannot be empty" }
  }

  try {
    const client = createClient(clientOptions)
    const response = await client.tui.appendPrompt({
      body: { text },
    })

    if (response.error) {
      return {
        success: false,
        error: String(response.error),
      }
    }

    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    }
  }
}

/**
 * Submit the current prompt in the TUI
 *
 * Triggers execution of whatever text is currently in the prompt input.
 * Use after appendPrompt() for fully automated workflows.
 *
 * @param clientOptions - Client configuration
 * @returns Operation result
 *
 * @example
 * ```typescript
 * // Programmatically trigger prompt submission
 * await appendPrompt("Run the build")
 * await submitPrompt()
 * ```
 */
export async function submitPrompt(
  clientOptions: ClientOptions = {}
): Promise<TuiOperationResult> {
  try {
    const client = createClient(clientOptions)
    const response = await client.tui.submitPrompt({})

    if (response.error) {
      return {
        success: false,
        error: String(response.error),
      }
    }

    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    }
  }
}

/**
 * Execute a slash command in the TUI
 *
 * Runs slash commands externally without needing to type them.
 * Useful for IDE integrations and automation scripts.
 *
 * @param command - Command name (with or without leading slash)
 * @param clientOptions - Client configuration
 * @returns Operation result
 *
 * @example
 * ```typescript
 * // Execute slash commands programmatically
 * await executeCommand("session_new")     // Start new session
 * await executeCommand("/compact")        // Compact context
 * await executeCommand("line-prep")       // Run line-cook prep
 * ```
 */
export async function executeCommand(
  command: string,
  clientOptions: ClientOptions = {}
): Promise<TuiOperationResult> {
  // Normalize command (remove leading slash if present)
  const normalizedCommand = command.startsWith("/") ? command.slice(1) : command

  if (!normalizedCommand) {
    return { success: false, error: "Command cannot be empty" }
  }

  try {
    const client = createClient(clientOptions)

    const response = await client.tui.executeCommand({
      body: { command: normalizedCommand },
    })

    if (response.error) {
      return {
        success: false,
        error: String(response.error),
      }
    }

    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    }
  }
}

/**
 * Display a toast notification in the TUI
 *
 * Shows temporary notifications to the user.
 * Useful for status updates, warnings, and confirmations.
 *
 * @param options - Toast configuration
 * @param clientOptions - Client configuration
 * @returns Operation result
 *
 * @example
 * ```typescript
 * // Show success notification
 * await showToast({
 *   title: "Build Complete",
 *   message: "All tests passed",
 *   variant: "success"
 * })
 *
 * // Show warning without title
 * await showToast({
 *   message: "Context nearing limit",
 *   variant: "warning",
 *   duration: 10000
 * })
 * ```
 */
export async function showToast(
  options: ToastOptions,
  clientOptions: ClientOptions = {}
): Promise<TuiOperationResult> {
  if (!options.message || !options.message.trim()) {
    return { success: false, error: "Message cannot be empty" }
  }

  const duration = options.duration ?? 5000
  if (duration < 0) {
    return { success: false, error: "Duration must be non-negative" }
  }

  try {
    const client = createClient(clientOptions)
    const response = await client.tui.showToast({
      body: {
        title: options.title,
        message: options.message,
        variant: options.variant ?? "info",
        duration,
      },
    })

    if (response.error) {
      return {
        success: false,
        error: String(response.error),
      }
    }

    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    }
  }
}

/**
 * Clear the current prompt in the TUI
 *
 * Removes any text from the prompt input.
 * Useful before setting a new prompt programmatically.
 *
 * @param clientOptions - Client configuration
 * @returns Operation result
 *
 * @example
 * ```typescript
 * // Clear and set new prompt
 * await clearPrompt()
 * await appendPrompt("New task: ...")
 * ```
 */
export async function clearPrompt(
  clientOptions: ClientOptions = {}
): Promise<TuiOperationResult> {
  try {
    const client = createClient(clientOptions)
    const response = await client.tui.clearPrompt({})

    if (response.error) {
      return {
        success: false,
        error: String(response.error),
      }
    }

    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    }
  }
}

/**
 * Open the help dialog in the TUI
 *
 * @param clientOptions - Client configuration
 * @returns Operation result
 */
export async function openHelp(
  clientOptions: ClientOptions = {}
): Promise<TuiOperationResult> {
  try {
    const client = createClient(clientOptions)
    const response = await client.tui.openHelp({})

    if (response.error) {
      return {
        success: false,
        error: String(response.error),
      }
    }

    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    }
  }
}

/**
 * Open the session selector in the TUI
 *
 * @param clientOptions - Client configuration
 * @returns Operation result
 */
export async function openSessions(
  clientOptions: ClientOptions = {}
): Promise<TuiOperationResult> {
  try {
    const client = createClient(clientOptions)
    const response = await client.tui.openSessions({})

    if (response.error) {
      return {
        success: false,
        error: String(response.error),
      }
    }

    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    }
  }
}

/**
 * Open the theme selector in the TUI
 *
 * @param clientOptions - Client configuration
 * @returns Operation result
 */
export async function openThemes(
  clientOptions: ClientOptions = {}
): Promise<TuiOperationResult> {
  try {
    const client = createClient(clientOptions)
    const response = await client.tui.openThemes({})

    if (response.error) {
      return {
        success: false,
        error: String(response.error),
      }
    }

    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    }
  }
}

/**
 * Open the model selector in the TUI
 *
 * @param clientOptions - Client configuration
 * @returns Operation result
 */
export async function openModels(
  clientOptions: ClientOptions = {}
): Promise<TuiOperationResult> {
  try {
    const client = createClient(clientOptions)
    const response = await client.tui.openModels({})

    if (response.error) {
      return {
        success: false,
        error: String(response.error),
      }
    }

    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    }
  }
}

/**
 * Set the prompt text (clear and append in one operation)
 *
 * Convenience function that clears the current prompt and sets new text.
 *
 * @param text - Text to set as the prompt
 * @param clientOptions - Client configuration
 * @returns Operation result
 *
 * @example
 * ```typescript
 * // Replace the current prompt
 * await setPrompt("Run lint and fix issues")
 * ```
 */
export async function setPrompt(
  text: string,
  clientOptions: ClientOptions = {}
): Promise<TuiOperationResult> {
  const clearResult = await clearPrompt(clientOptions)
  if (!clearResult.success) {
    return clearResult
  }

  return appendPrompt(text, clientOptions)
}

/**
 * Send a prompt (set and submit in one operation)
 *
 * Convenience function that sets the prompt and immediately submits it.
 * For fire-and-forget automation.
 *
 * @param text - Prompt text to send
 * @param clientOptions - Client configuration
 * @returns Operation result
 *
 * @example
 * ```typescript
 * // Send a prompt immediately
 * await sendTuiPrompt("Run the test suite")
 * ```
 */
export async function sendTuiPrompt(
  text: string,
  clientOptions: ClientOptions = {}
): Promise<TuiOperationResult> {
  const setResult = await setPrompt(text, clientOptions)
  if (!setResult.success) {
    return setResult
  }

  return submitPrompt(clientOptions)
}
