<!-- @format -->

# Coding Agent Instructions

**Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

## Guidelines for Code Changes

**MINIMAL CHANGES ONLY**: Make the smallest possible changes to address the specific request. Do NOT modify files that are not directly related to the task:

- **Package files** (`package.json`, `package-lock.json`) should only be modified if explicitly required for the feature being worked on
- **Build artifacts** and **symlinks** should not be committed unless they are the direct target of the request
- **Repository setup** (symlinks, environment bootstrapping) should be done for development/testing only, not committed
- **Infrastructure changes** should be avoided unless they are specifically requested

When working on feature requests:

1. Identify the **exact files** that need to be modified for the request
2. Make changes **only** to those files
3. Use temporary setup for development/testing but revert any unrelated changes before committing
4. Focus on the **specific feature or fix** requested, not general repository improvements

## Guidelines for Commit Messages

- Title and description must follow conventional commit format: start with a type followed by a colon and a brief summary starting with an imperative verb.
- Type must follow configured types in root package.json or default to standard types.
- Add a scope in parentheses if project structure warrants it (check for workspace, modules or package names)
