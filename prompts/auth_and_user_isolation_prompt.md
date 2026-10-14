# ProofLens AI — Critical Fix: Independent User Registration, Login & Data Isolation

## Objective

Fix the existing authentication and user-isolation system in the ProofLens AI repository. The application must support genuine, independent accounts for every user.

Currently, signing in with an email and password displays an "Incorrect email or password" error, and independent user accounts are still not working as expected.

Do not assume the cause. Audit the actual code, trace the complete authentication flow, identify the confirmed root causes, and implement the necessary fixes.

## 1. Audit the Complete Authentication Flow

Trace the entire flow across the existing frontend, FastAPI backend, database models, authentication services, and API integration.

Verify:

- User registration and account creation.
- Password hashing and password verification.
- Login API request and response schemas.
- Frontend API base URL and endpoint configuration.
- Database user creation, persistence, and retrieval.
- Email normalization and duplicate-account handling.
- JWT creation, expiration, validation, and authenticated-user resolution.
- Frontend session initialization, token persistence, and logout.
- Database migrations and schema compatibility.
- Backend errors and frontend error handling.

Determine why a newly registered user cannot reliably sign in. Check for mismatched API contracts, inconsistent password hashing, incorrect database queries, missing persistence, configuration mismatches, and frontend/backend integration errors.

Do not implement speculative fixes without tracing the actual failure.

## 2. Independent User Registration

Every new user must be able to create an independent account using their own email address and password.

Requirements:

- Each user must have a unique, persistent database identity.
- Store passwords only as secure password hashes using an appropriate password-hashing algorithm.
- Never store or log plaintext passwords.
- Enforce email uniqueness at both the application and database levels.
- Normalize email addresses consistently during registration and login.
- Reject duplicate registrations with a clear, user-friendly message.
- Persist accounts in PostgreSQL so they survive application restarts.
- Never use an in-memory dictionary, mock user, or browser-only state as the authoritative user database.
- Ensure a newly registered account can successfully log in using its registered credentials.
- If email verification is already part of the intended authentication flow, preserve and correctly integrate it rather than bypassing it.

## 3. Strict Per-User Data Isolation

A user must never access another user's private data.

Enforce authenticated ownership and authorization on the backend for:

- Documents and uploaded PDFs.
- Workspaces and workspace memberships.
- Conversations and chat history.
- Document processing jobs and ingestion status.
- RAG queries and retrieved evidence.
- Citations and source references.
- Analytics and usage information.
- Any other user-owned resources in the existing application.

Every protected API operation must derive the authenticated user identity from the validated authentication context and enforce ownership or explicit workspace membership.

Do not trust a user ID, workspace ID, document ID, or ownership claim supplied by the frontend without backend authorization checks.

Do not return global documents, shared chat history, or another user's records by default.

Use the existing database relationships and architecture where possible. Add or correct database constraints, relationships, queries, and migrations when required.

## 4. Session and Authentication Reliability

- Ensure registration and login return consistent responses matching the frontend API contract.
- Ensure JWTs identify the correct database user.
- Ensure authenticated requests consistently resolve to the correct user.
- Handle expired or invalid tokens safely.
- Ensure logout clears the appropriate client session.
- Ensure switching accounts cannot expose the previous user's data.
- Ensure a failed login does not create an authenticated session.
- Remove automatic demo login from normal authentication flows if it bypasses real authentication or creates shared-account exposure.
- Keep demo functionality separate and explicitly opt-in if it is retained.

Do not weaken authentication or authorization to make login appear successful.

## 5. Database and Configuration

Inspect the existing database configuration and deployment setup.

- Confirm registration and login use the intended persistent database.
- Ensure frontend and backend use the correct API configuration.
- Check that development and production environments do not unintentionally use different databases or incompatible authentication settings.
- Use migrations for schema changes when appropriate.
- Prevent insecure default authentication secrets from being accepted in production.
- Keep configuration environment-driven and avoid hardcoding credentials, secrets, URLs, or user identities.

Never access, read, print, modify, overwrite, or delete any `.env` file or secret value. You may inspect configuration code and variable names without exposing secret values.

## 6. Preserve the Existing UI/UX

Do not redesign the application.

Preserve the current ProofLens AI visual design, login modal, typography, colors, layout, buttons, navigation, and responsive behavior.

Only make frontend changes necessary to correct authentication, registration, session handling, loading states, and meaningful error messages.

Ensure the Create Account action actually creates a persistent account and that Sign In authenticates that account.

## 7. Required Verification

Run the available tests and add targeted tests where necessary.

Verify these scenarios using isolated test accounts and a test database:

1. User A registers with a unique email and password.
2. User A logs in using those credentials.
3. User B registers independently with a different email and password.
4. User B logs in successfully.
5. Both accounts remain available after a backend restart.
6. User A cannot access User B's documents, chats, workspaces, or analytics.
7. User B cannot access User A's private resources.
8. Invalid passwords are rejected.
9. Duplicate email registration is rejected.
10. Invalid and expired tokens cannot access protected resources.
11. Logging out and switching accounts does not leak the previous session's data.
12. Unauthenticated users cannot access protected endpoints.

Use automated tests and API/database verification wherever possible. Do not claim a scenario passes unless it was actually tested.

Do not use real user data or modify production records during verification.

## 8. Final Report

After implementation, report:

- Confirmed root cause or root causes of the authentication failure.
- Files changed and the reason for each change.
- Database migrations or schema changes introduced.
- Registration and login verification results.
- Per-user isolation test results.
- Tests passed, failed, or not run.
- Any remaining blockers or manual setup requirements.

Do not merely provide recommendations. Implement and verify the fixes in the existing repository.

## Non-Negotiable Rules

- Do not redesign the existing UI/UX.
- Do not hardcode users, credentials, secrets, or environment-specific URLs.
- Do not bypass authentication or authorization.
- Do not expose one user's data to another user.
- Do not access or modify `.env` files or secret values.
- Do not commit, push, or deploy changes.
- Fix the actual root cause rather than hiding the login error.
- Keep the implementation flexible for future ProofLens AI features.
