# Copilot Instructions

Language: Python (using uv package manager with env managed by uv .venv)

General Rules
- Do not be verbose
- Clarity over cleverness
- Follow Python best practices
- Write reusable focused functions
- Keep UI and logic separate
- Avoid global state, or put it in a singleton

Code Quality
- Type everything
- Handle errors explicitly
- Never ignore subprocess failures
- No magic numbers
- No hardcoded strings without constants

Testing
- Write tests for every function
- Mock adb interactions
- Tests must be deterministic
- No flaky tests
- UI logic should be testable via state

UX
- Never block the UI thread
- Always show feedback
- Always show keybindings
- No destructive action without confirmation

Commits
- Commit only when tests pass
- Keep commits small
- Use concise imperative commit messages (feat:, fix:, chore:, docs:, test:)
- One logical change per commit

Packaging
- Ensure code works when frozen
- Avoid dynamic imports
- Avoid filesystem assumptions

Style
- Use black formatting
- Use ruff for linting
- Use mypy for types
- Keep files small and focused

Workflow
- Understand the full context before coding (outline.md, checklist.md, requirements.md)
- Pick next tasks from checklist.md
- Write code only for the selected task
- Write and run all tests for the task
- Update checklist.md to mark task done
- Commit changes (logical commits per task)
