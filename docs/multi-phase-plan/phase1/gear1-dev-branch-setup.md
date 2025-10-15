# Gear 1: Dev Branch Setup (Interim Solution)

## Problem

Gear 1 currently creates PRs that merge to `main`, which pollutes the moderator repository with generated code. This is a known architectural flaw that will be fixed in Gear 2.

## Interim Solution

**Use a `dev` branch as the target for all Gear 1 generated code PRs.**

This keeps `main` clean while still allowing Gear 1 to function end-to-end.

---

## Setup Instructions

### 1. Create the `dev` Branch

```bash
cd ~/moderator

# Ensure you're on main
git checkout main
git pull

# Create dev branch from main
git checkout -b dev

# Push dev branch to remote
git push -u origin dev

# Return to main
git checkout main
```

### 2. Verify Setup

```bash
# Check that both branches exist
git branch -a
# Should show:
#   main
#   dev
#   remotes/origin/main
#   remotes/origin/dev
```

### 3. Run Moderator (It Will Now Use `dev`)

```bash
# The code has been updated to use dev by default
python main.py "Create a calculator CLI"

# When asked "Proceed with execution? (yes/no):", answer: yes

# PRs will now be created against dev branch instead of main
```

---

## How It Works

### Code Changes Made

**[src/git_manager.py:83](../src/git_manager.py#L83)**
```python
def create_pr(self, task: Task, base_branch: str = "dev") -> tuple[str, int]:
    """
    Create pull request via GitHub CLI

    Args:
        task: Task object containing PR details
        base_branch: Base branch to merge into (default: "dev" for Gear 1)

    Note: Gear 1 uses "dev" branch to avoid polluting main.
          Gear 2 will use proper target repository architecture.
    """
    # ...
    result = subprocess.run(
        ["gh", "pr", "create",
         "--base", base_branch,  # <-- PRs now target dev
         "--title", f"Task {task.id}: {task.description[:50]}",
         "--body", pr_body],
        # ...
    )
```

### Workflow

```
main branch (stays clean)
    ↓
dev branch (created from main)
    ↓
feature branch: moderator-gear1/task-001
    ↓
PR created: feature branch → dev (not main!)
    ↓
[YOU REVIEW & MERGE PR TO DEV]
    ↓
dev branch gets updated with generated code
    ↓
main stays clean
```

---

## Working with Dev Branch

### Merging PRs

When moderator creates a PR:

1. Review the PR on GitHub
2. **Merge to `dev`** (not `main`)
3. Press ENTER in terminal to continue

### Keeping Dev in Sync with Main

Periodically sync `dev` with `main` to get infrastructure updates:

```bash
git checkout dev
git merge main
git push
```

### When You Want to Promote to Main

If you want to move generated code from `dev` to `main` (not recommended for Gear 1):

```bash
# Review what's in dev
git checkout dev
git log --oneline

# Merge specific commits to main
git checkout main
git cherry-pick <commit-hash>
git push
```

**Note:** It's better to keep `dev` separate and only merge moderator infrastructure changes to `main`.

---

## Cleanup (Optional)

If you have old branches/PRs from before this change:

```bash
# List all moderator-gear1 branches
git branch -a | grep moderator-gear1

# Delete local branches
git branch -D moderator-gear1/task-001
git branch -D moderator-gear1/task-002

# Delete remote branches
git push origin --delete moderator-gear1/task-001
git push origin --delete moderator-gear1/task-002

# Close old PRs on GitHub that target main
# (Do this manually via GitHub UI)
```

---

## Testing the Setup

### Test 1: Verify Dev Branch Exists

```bash
gh repo view --json defaultBranch,name
# Should show main as default

git branch -a | grep dev
# Should show dev branch
```

### Test 2: Run a Test Project

```bash
python main.py "Create a simple hello world CLI"
# Answer "yes" when prompted

# Verify PR is created against dev:
gh pr list
# Should show PR with base: dev (not main)
```

### Test 3: Merge and Continue

1. Go to GitHub and merge the PR to `dev`
2. Press ENTER in terminal
3. Moderator should continue to next task
4. Verify next PR also targets `dev`

---

## Benefits of This Approach

✅ **Main branch stays clean** - No generated code pollutes infrastructure
✅ **Gear 1 still works end-to-end** - Full workflow with PRs and merges
✅ **Easy to test** - Can experiment without affecting main
✅ **Easy cleanup** - Delete dev branch later if needed
✅ **Minimal code changes** - Just one parameter added

---

## Limitations (Fixed in Gear 2)

❌ Still operates in moderator repo (not target repo)
❌ Still mixes infrastructure and generated code (just in dev instead of main)
❌ Still can't use on multiple projects simultaneously
❌ State still stored in moderator repo

**These will be fixed in Gear 2** with the `.moderator/` embedded workspace architecture (see [design-issue-separation-of-concerns.md](design-issue-separation-of-concerns.md)).

---

## Reverting to Main (If Needed)

If you want to temporarily use `main` as the base branch:

**Option 1: Edit config**
```yaml
# config/config.yaml
git:
  base_branch: "main"  # Override default "dev"
```

**Option 2: Edit code temporarily**
```python
# src/git_manager.py:83
def create_pr(self, task: Task, base_branch: str = "main"):  # Change to "main"
```

But it's recommended to keep `dev` for Gear 1.

---

## Summary

1. ✅ Create `dev` branch from `main`
2. ✅ Code updated to target `dev` by default
3. ✅ Run moderator normally
4. ✅ PRs now merge to `dev` instead of `main`
5. ✅ `main` stays clean until Gear 2

**Next Steps:**
- Test the workflow with a simple project
- Verify PRs target `dev` branch
- Keep `dev` as the testing ground for Gear 1 generated code
