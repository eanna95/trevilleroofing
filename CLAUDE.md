# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

For comprehensive project documentation, see:
- **[README.md](README.md)** - Complete project overview and quick start guide

## Status Tracking

Always maintain a `status.txt` file in the project root to track:
- Current work in progress
- Completed tasks
- Planned work and priorities
- Important notes and decisions

**Important**: Keep only the last 7 days worth of updates in status.txt to maintain readability and focus on recent work. Archive older entries by removing them when adding new content.

Update this file at the start of each work session and whenever tasks are completed or plans change. This ensures continuity across sessions and provides a clear audit trail of recent project evolution.

## Communication Guidelines

When user requests are unclear, ambiguous, or require additional context:
- Always ask follow-up questions to clarify requirements
- Ask about preferred approaches when multiple options exist
- Request priority guidance when multiple tasks are involved
- Seek clarification on scope and expected outcomes
- Don't make assumptions - ask for specifics

## Development Notes

### Testing Strategy
- Use small test videos from `test_scripts/` directory for development
- All test files should be kept in the `test_scripts/` directory

### Error Handling
Scripts implement comprehensive error handling for:
- Missing input files and invalid paths

### Line Ending Compatibility (WSL/Windows)
When creating shell scripts or other executable files in WSL environments that interact with Windows filesystems:

**Problem**: Files created may have Windows line endings (CRLF) which cause execution errors:
```
-bash: ./script.sh: /bin/bash^M: bad interpreter: No such file or directory
```

**Solutions**:
1. **Fix existing files**: Use `dos2unix filename.sh` to convert line endings
2. **Prevention**: When creating new shell scripts, always run `dos2unix` after creation
3. **Alternative**: Use `sed -i 's/\r$//' filename.sh` if dos2unix is unavailable

**Best Practice**: After creating any executable script file, immediately run:
```bash
dos2unix filename.sh
chmod +x filename.sh
```

**CRITICAL REMINDER**: This is a recurring problem in this WSL/Windows environment. **ALWAYS** run `dos2unix` on ALL newly created files (shell scripts, Dockerfiles, YAML files, etc.) to prevent execution errors. **Only run dos2unix when creating NEW files - not when editing existing files.** When creating multiple new files, use:
```bash
# Fix line endings for all relevant NEW files at once
```

This ensures proper line endings and executable permissions for cross-platform compatibility.

## Code Organization and Principles

### DRY (Don't Repeat Yourself) Principles
The codebase follows DRY principles to minimize code duplication and improve maintainability:

- **Shared utilities**: Common functionality is centralized in the `utils/` package
- **Reusable functions**: Keep functions short, focused, and easily testable
- **Consistent interfaces**: Similar operations use the same patterns across tools
- **Modular design**: Break complex operations into smaller, composable functions

**Function Guidelines:**
- Functions should do one thing well (Single Responsibility Principle)
- Keep functions under 50 lines when possible for readability
- Use descriptive names that clearly indicate the function's purpose
- Avoid deep nesting - prefer early returns and guard clauses
- Extract common patterns into shared utility functions

### Shared Utilities (utils/ package)

The `utils/` package contains shared functionality used across all tools. This is the designated location for all shared code, utility functions, and common tools.

#### Code Organization Standards
**Function Length**: Keep functions under 10-15 lines when possible for readability and maintainability.

**DRY Principles**: Avoid code duplication by extracting common patterns into shared utility functions.

**Single Responsibility**: Functions should do one thing well and have descriptive names that clearly indicate their purpose.

**Module Organization**: Break functionality into focused modules within the utils package:

### Utils Organization Standards
- **Modular Design**: Break complex operations into smaller, composable functions
- **Consistent Interfaces**: Similar operations use the same patterns across tools
- **Error Handling**: All utility functions include proper error handling and logging
- **Reusability**: Functions are designed to be used across multiple scripts
- **Documentation**: Each utility function has clear docstrings explaining purpose and parameters

This structure ensures consistent behavior, reduces code duplication, and maintains high code quality across the video processing pipeline.
