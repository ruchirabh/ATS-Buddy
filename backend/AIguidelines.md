# AI Coding Guidelines

## Core Principles
- Keep functions small and testable
- Separate routes and services
- No business logic in routes
- Use environment variables
- Avoid hardcoded secrets
- Use blueprints for route grouping
- Keep models separate
- Use config class pattern
- Prefer explicit imports

## Logging Rules (CRITICAL)
- EVERY API endpoint MUST log:
  - 📥 "INCOMING REQUEST: {method} {path}" at the start
  - 📦 "REQUEST PAYLOAD: {payload}" (with passwords masked as '********')
  - 📤 "RESPONSE: {status} - {message}" at the end
  - Use emojis for visual distinction (📥, 📦, 📤, ✅, ❌, ⚠️)
  - Log user email for auth operations
  - Never log raw passwords
  - Use appropriate log levels (INFO, WARNING, ERROR)

## Error Handling
- Always return consistent JSON: {success: boolean, error?: string, data?: any}
- Log errors with stack traces
- Sanitize error messages for client responses
- Never expose internal error details to client