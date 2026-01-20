/**
 * Unit tests for permission utilities
 *
 * Tests the permission auto-approval logic for safe operations.
 */
import { describe, test, expect } from "bun:test"
import {
  isSafeBashCommand,
  isDangerousCommand,
  shouldAutoApprove,
  SAFE_BASH_PATTERNS,
  SAFE_BASH_EXCLUSIONS,
  SAFE_TOOL_TYPES,
  DANGEROUS_PATTERNS,
} from "../../src/permission-utils"
import type { Permission } from "@opencode-ai/sdk"

/**
 * Create a mock Permission object
 */
function createMockPermission(overrides: Partial<Permission> = {}): Permission {
  return {
    id: "mock-permission-id",
    type: "bash",
    sessionID: "mock-session-id",
    messageID: "mock-message-id",
    title: "Mock Permission",
    metadata: {},
    time: { created: Date.now() },
    ...overrides,
  }
}

describe("Permission Utils", () => {
  describe("isSafeBashCommand", () => {
    describe("file reading commands", () => {
      test.each([
        ["cat file.txt", true],
        ["head -n 10 file.txt", true],
        ["tail -f logs.txt", true],
        ["less file.txt", true],
        ["more file.txt", true],
        ["file myfile", true],
        ["wc -l file.txt", true],
        ["stat file.txt", true],
      ])("'%s' should be safe: %s", (command, expected) => {
        expect(isSafeBashCommand(command)).toBe(expected)
      })
    })

    describe("directory listing commands", () => {
      test.each([
        ["ls", true],
        ["ls -la", true],
        ["ls -la /home", true],
        ["dir", true],
        ["tree", true],
        ["tree -L 2", true],
        ["pwd", true],
      ])("'%s' should be safe: %s", (command, expected) => {
        expect(isSafeBashCommand(command)).toBe(expected)
      })
    })

    describe("search commands", () => {
      test.each([
        ["grep pattern file.txt", true],
        ["grep -r pattern .", true],
        ["rg pattern", true],
        ["rg -i pattern src/", true],
        ["find . -type f", true],
        ["find . -name '*.ts'", true],
        ["which node", true],
        ["whereis python", true],
        ["locate file.txt", true],
        ["fd pattern", true],
      ])("'%s' should be safe: %s", (command, expected) => {
        expect(isSafeBashCommand(command)).toBe(expected)
      })
    })

    describe("git read-only commands", () => {
      test.each([
        ["git status", true],
        ["git log", true],
        ["git log --oneline -10", true],
        ["git diff", true],
        ["git diff HEAD~1", true],
        ["git show HEAD", true],
        ["git branch", true],
        ["git branch -a", true],
        ["git remote -v", true],
        ["git tag", true],
        ["git describe", true],
        ["git rev-parse HEAD", true],
        ["git ls-files", true],
        ["git blame file.ts", true],
      ])("'%s' should be safe: %s", (command, expected) => {
        expect(isSafeBashCommand(command)).toBe(expected)
      })
    })

    describe("beads read-only commands", () => {
      test.each([
        ["bd list", true],
        ["bd list --status=open", true],
        ["bd show lc-123", true],
        ["bd ready", true],
        ["bd blocked", true],
        ["bd stats", true],
        ["bd search query", true],
        ["bd sync --status", true],
        ["bd doctor", true],
      ])("'%s' should be safe: %s", (command, expected) => {
        expect(isSafeBashCommand(command)).toBe(expected)
      })
    })

    describe("system info commands", () => {
      test.each([
        ["date", true],
        ["whoami", true],
        ["hostname", true],
        ["uname", true],
        ["uname -a", true],
        ["env", true],
        ["printenv", true],
        ["echo $HOME", true],
        ["echo $PATH", true],
      ])("'%s' should be safe: %s", (command, expected) => {
        expect(isSafeBashCommand(command)).toBe(expected)
      })
    })

    describe("package manager query commands", () => {
      test.each([
        ["npm list", true],
        ["npm ls", true],
        ["npm view package", true],
        ["npm info package", true],
        ["npm outdated", true],
        ["bun pm ls", true],
        ["pip list", true],
        ["pip show package", true],
        ["cargo tree", true],
        ["go list", true],
      ])("'%s' should be safe: %s", (command, expected) => {
        expect(isSafeBashCommand(command)).toBe(expected)
      })
    })

    describe("unsafe commands (should NOT be safe)", () => {
      test.each([
        ["rm file.txt", false],
        ["rm -rf dir/", false],
        ["mv file.txt dest/", false],
        ["cp file.txt dest/", false],
        ["echo 'content' > file.txt", false],
        ["git add .", false],
        ["git commit -m 'msg'", false],
        ["git push", false],
        ["npm install", false],
        ["npm run build", false],
        ["bd create --title='test'", false],
        ["bd update lc-123 --status=closed", false],
        ["bd close lc-123", false],
        ["bd sync", false], // bd sync without --status modifies state
        ["mkdir newdir", false],
        ["touch newfile.txt", false],
        ["chmod 755 file.sh", false],
      ])("'%s' should NOT be safe: %s", (command, expected) => {
        expect(isSafeBashCommand(command)).toBe(expected)
      })
    })

    describe("exclusion patterns (potentially safe commands made unsafe)", () => {
      test.each([
        ["find . -name '*.ts' -exec rm {} \\;", false], // find with -exec
        ["find . -type f -delete", false], // find with -delete
        ["find . -name '*.tmp' -ok rm {} \\;", false], // find with -ok
        ["cat file.txt | rm -rf", false], // pipe to rm (not realistic but blocked)
        ["ls | xargs rm", false], // pipe to xargs rm
        ["cat file.txt | tee output.txt", false], // pipe to tee (writes file)
        ["ls > output.txt", false], // output redirection
        ["cat file >> output.txt", false], // append redirection
      ])("'%s' should NOT be safe (exclusion): %s", (command, expected) => {
        expect(isSafeBashCommand(command)).toBe(expected)
      })
    })
  })

  describe("isDangerousCommand", () => {
    describe("dangerous commands", () => {
      test.each([
        ["git push --force origin main", true],
        ["git push -f origin main", false], // Only --force is matched
        ["git reset --hard HEAD~1", true],
        ["rm -rf /", true],
        ["rm -rf /*", true],
        ["rm -rf /home", true],
        ["rm -rf /etc", true],
        ["rm -rf ~", true],
        ["rm -rf $HOME", true],
        ["rm -rf %USERPROFILE%", true],
        ["format C:", true],
        ["mkfs.ext4 /dev/sda1", true],
        ["dd if=/dev/zero of=/dev/sda", true],
      ])("'%s' should be dangerous: %s", (command, expectedDangerous) => {
        const result = isDangerousCommand(command)
        expect(result.dangerous).toBe(expectedDangerous)
        if (expectedDangerous) {
          expect(result.pattern).toBeDefined()
        }
      })
    })

    describe("non-dangerous commands", () => {
      test.each([
        "ls -la",
        "git status",
        "git push origin main",
        "git reset HEAD~1",
        "rm file.txt",
        "rm -rf ./build",
        "npm install",
      ])("'%s' should NOT be dangerous", (command) => {
        const result = isDangerousCommand(command)
        expect(result.dangerous).toBe(false)
      })
    })
  })

  describe("shouldAutoApprove", () => {
    describe("safe tool types", () => {
      test.each([
        ["read", "allow"],
        ["glob", "allow"],
        ["grep", "allow"],
        ["list", "allow"],
        ["search", "allow"],
      ] as const)("tool type '%s' should be %s", (toolType, expected) => {
        const permission = createMockPermission({ type: toolType })
        expect(shouldAutoApprove(permission)).toBe(expected)
      })
    })

    describe("bash commands via pattern", () => {
      test("safe command in pattern string should be allowed", () => {
        const permission = createMockPermission({
          type: "bash",
          pattern: "ls -la",
        })
        expect(shouldAutoApprove(permission)).toBe("allow")
      })

      test("safe command in pattern array should be allowed", () => {
        const permission = createMockPermission({
          type: "bash",
          pattern: ["git status"],
        })
        expect(shouldAutoApprove(permission)).toBe("allow")
      })

      test("unsafe command should ask", () => {
        const permission = createMockPermission({
          type: "bash",
          pattern: "npm install",
        })
        expect(shouldAutoApprove(permission)).toBe("ask")
      })

      test("dangerous command should be denied", () => {
        const permission = createMockPermission({
          type: "bash",
          pattern: "rm -rf /",
        })
        expect(shouldAutoApprove(permission)).toBe("deny")
      })
    })

    describe("bash commands via metadata", () => {
      test("safe command in metadata.command should be allowed", () => {
        const permission = createMockPermission({
          type: "bash",
          metadata: { command: "git diff" },
        })
        expect(shouldAutoApprove(permission)).toBe("allow")
      })

      test("safe command in metadata.cmd should be allowed", () => {
        const permission = createMockPermission({
          type: "bash",
          metadata: { cmd: "bd show lc-123" },
        })
        expect(shouldAutoApprove(permission)).toBe("allow")
      })
    })

    describe("shell type", () => {
      test("safe command with shell type should be allowed", () => {
        const permission = createMockPermission({
          type: "shell",
          pattern: "pwd",
        })
        expect(shouldAutoApprove(permission)).toBe("allow")
      })
    })

    describe("edge cases", () => {
      test("bash with no command should ask", () => {
        const permission = createMockPermission({
          type: "bash",
          pattern: undefined,
          metadata: {},
        })
        expect(shouldAutoApprove(permission)).toBe("ask")
      })

      test("unknown tool type should ask", () => {
        const permission = createMockPermission({
          type: "unknown_tool",
          pattern: "anything",
        })
        expect(shouldAutoApprove(permission)).toBe("ask")
      })

      test("edit tool should ask", () => {
        const permission = createMockPermission({
          type: "edit",
          pattern: "/path/to/file.ts",
        })
        expect(shouldAutoApprove(permission)).toBe("ask")
      })

      test("write tool should ask", () => {
        const permission = createMockPermission({
          type: "write",
          pattern: "/path/to/file.ts",
        })
        expect(shouldAutoApprove(permission)).toBe("ask")
      })
    })
  })

  describe("pattern arrays are non-empty", () => {
    test("SAFE_BASH_PATTERNS has entries", () => {
      expect(SAFE_BASH_PATTERNS.length).toBeGreaterThan(0)
    })

    test("SAFE_BASH_EXCLUSIONS has entries", () => {
      expect(SAFE_BASH_EXCLUSIONS.length).toBeGreaterThan(0)
    })

    test("SAFE_TOOL_TYPES has entries", () => {
      expect(SAFE_TOOL_TYPES.size).toBeGreaterThan(0)
    })

    test("DANGEROUS_PATTERNS has entries", () => {
      expect(DANGEROUS_PATTERNS.length).toBeGreaterThan(0)
    })
  })
})
