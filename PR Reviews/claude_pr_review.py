#!/usr/bin/env python3
"""
Claude PR Review Script for Bitbucket Server
Fetches PR diff and posts an AI-generated review as a comment.

Required Environment Variables:
  BITBUCKET_URL       - Base URL e.g. https://bitbucket.yourcompany.com:8443
  BITBUCKET_TOKEN     - Personal Access Token (store as a secured pipeline variable)
  ANTHROPIC_API_KEY   - Anthropic API key (store as a secured pipeline variable)
  BITBUCKET_PROJECT   - Project key e.g. SCPS
  BITBUCKET_REPO      - Repo slug e.g. vipa7
  BITBUCKET_PR_ID     - PR ID (auto-set by Bitbucket Pipelines as $BITBUCKET_PR_ID)
"""

import os
import sys
import json
import requests
import anthropic

# ── Config ────────────────────────────────────────────────────────────────────

BB_URL      = os.environ["BITBUCKET_URL"].rstrip("/")
BB_TOKEN    = os.environ["BITBUCKET_TOKEN"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
PROJECT     = os.environ.get("BITBUCKET_PROJECT", "SCPS")
REPO        = os.environ.get("BITBUCKET_REPO", "vipa7")
PR_ID       = os.environ["BITBUCKET_PR_ID"]

HEADERS = {
    "Authorization": f"Bearer {BB_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_pr_info():
    """Fetch PR metadata (title, description, author)."""
    url = f"{BB_URL}/rest/api/1.0/projects/{PROJECT}/repos/{REPO}/pull-requests/{PR_ID}"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_pr_diff():
    """Fetch the unified diff for the PR."""
    url = f"{BB_URL}/rest/api/1.0/projects/{PROJECT}/repos/{REPO}/pull-requests/{PR_ID}/diff"
    resp = requests.get(url, headers=HEADERS, timeout=60, params={"contextLines": 5})
    resp.raise_for_status()
    data = resp.json()

    # Convert Bitbucket diff JSON → unified diff text
    lines = []
    for diff_file in data.get("diffs", []):
        src = diff_file.get("source", {}).get("toString", "")
        dst = diff_file.get("destination", {}).get("toString", "")
        lines.append(f"\n--- {src}\n+++ {dst}")
        for hunk in diff_file.get("hunks", []):
            lines.append(
                f"@@ -{hunk['sourceLine']},{hunk['sourceSpan']} "
                f"+{hunk['destinationLine']},{hunk['destinationSpan']} @@"
            )
            for seg in hunk.get("segments", []):
                prefix = {"CONTEXT": " ", "ADDED": "+", "REMOVED": "-"}.get(seg["type"], " ")
                for line in seg.get("lines", []):
                    lines.append(f"{prefix}{line['line']}")

    return "\n".join(lines)


def get_pr_commits():
    """Fetch commit messages for extra context."""
    url = f"{BB_URL}/rest/api/1.0/projects/{PROJECT}/repos/{REPO}/pull-requests/{PR_ID}/commits"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    commits = resp.json().get("values", [])
    return [c.get("message", "").strip() for c in commits]


def build_prompt(pr_info, diff_text, commits):
    title       = pr_info.get("title", "")
    description = pr_info.get("description", "(no description)")
    author      = pr_info.get("author", {}).get("user", {}).get("displayName", "Unknown")
    commit_log  = "\n".join(f"  - {m}" for m in commits) or "  (none)"

    return f"""You are an expert code reviewer. Please review the following pull request thoroughly.

## PR Details
- **Title:** {title}
- **Author:** {author}
- **Description:** {description}

## Commit Messages
{commit_log}

## Diff
```diff
{diff_text}
```

## Your Review

Provide a structured review with the following sections:

### ✅ Summary
Brief overview of what this PR does and your overall assessment.

### 🔍 Code Quality
Comment on code clarity, naming, structure, and adherence to good practices.

### 🐛 Bugs / Issues
List any bugs, logic errors, edge cases, or potential runtime issues. Be specific about file and line context.

### 🔒 Security
Flag any security concerns (injection, auth issues, exposed secrets, unsafe operations, etc.).

### ⚡ Performance
Note any inefficiencies, unnecessary allocations, blocking calls, or algorithmic concerns.

### 💡 Suggestions
Improvements that are not blocking but would enhance the code.

### ✔️ Verdict
End with one of: **APPROVE** / **REQUEST CHANGES** / **NEEDS DISCUSSION** and a one-line reason.
"""


def post_comment(review_text):
    """Post the review as a comment on the PR."""
    url = f"{BB_URL}/rest/api/1.0/projects/{PROJECT}/repos/{REPO}/pull-requests/{PR_ID}/comments"
    payload = {"text": f"## 🤖 Claude AI Code Review\n\n{review_text}"}
    resp = requests.post(url, headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"📥 Fetching PR #{PR_ID} from {BB_URL}...")
    pr_info = get_pr_info()
    print(f"   Title: {pr_info.get('title')}")

    print("📄 Fetching diff...")
    diff_text = get_pr_diff()
    if not diff_text.strip():
        print("⚠️  Empty diff — nothing to review.")
        sys.exit(0)

    # Truncate very large diffs to avoid exceeding token limits
    MAX_DIFF_CHARS = 60_000
    if len(diff_text) > MAX_DIFF_CHARS:
        diff_text = diff_text[:MAX_DIFF_CHARS] + "\n\n... [diff truncated due to size] ..."
        print(f"⚠️  Diff truncated to {MAX_DIFF_CHARS} characters.")

    print("📝 Fetching commits...")
    commits = get_pr_commits()

    print("🤖 Sending to Claude for review...")
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    prompt = build_prompt(pr_info, diff_text, commits)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    review_text = message.content[0].text
    print("✅ Review generated.")

    print("💬 Posting comment to PR...")
    result = post_comment(review_text)
    comment_id = result.get("id")
    print(f"✅ Review posted! Comment ID: {comment_id}")
    print(f"\n🔗 View PR: {BB_URL}/projects/{PROJECT}/repos/{REPO}/pull-requests/{PR_ID}")


if __name__ == "__main__":
    main()
