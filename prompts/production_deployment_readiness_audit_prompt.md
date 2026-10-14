# ProofLens AI — Production Deployment Readiness & Environment Configuration Audit

## Objective

Prepare the existing ProofLens AI repository for production deployment using the following architecture:

- **Database:** Supabase PostgreSQL with pgvector
- **Backend:** Python + FastAPI deployed on Render
- **Frontend:** Next.js deployed on Vercel
- **AI Provider:** Google Gemini for generation and embeddings
- **Document Storage:** Supabase Storage for persistent PDF files

Repository: `srushti-bore/ProofLens`

First, thoroughly inspect the current repository and its existing implementation. Then make only the changes required to prepare the project for reliable production deployment.

## 1. Strict Repository Rules

- Work only within the existing ProofLens repository.
- Do not rebuild the application from scratch.
- Preserve the current frontend UI/UX, layout, styling, components, animations, and design.
- Do not introduce duplicate implementations, configuration files, or unnecessary dependencies.
- Reuse the existing architecture and code wherever possible.
- Do not hardcode credentials, secrets, URLs, environment-specific values, or deployment-specific configuration.
- All environment-dependent settings must be configurable through environment variables.
- Keep the implementation flexible and maintainable for future enhancements.
- Do not commit, push, merge, or deploy anything. I will handle these steps manually.

## 2. CRITICAL ENVIRONMENT AND SECRET PROTECTION

You must NOT open, read, print, modify, overwrite, delete, or expose any actual `.env` files or their contents.

This restriction includes, but is not limited to:

- `.env`
- `.env.local`
- `.env.production`
- `backend/.env`
- `frontend/.env.local`
- Any other actual environment file containing local configuration or secrets.

Do not access or expose API keys, database passwords, JWT secrets, Supabase credentials, Gemini credentials, access tokens, or other sensitive values.

You may inspect existing `.env.example` and other explicitly named example/template files because they are intended to contain placeholders only.

Never copy real secret values into example files, source code, logs, documentation, terminal output, or Git-tracked files.

## 3. Audit the Existing Production Configuration

Inspect the current code and configuration to identify:

- Backend environment-variable definitions and validation.
- Frontend API base URL configuration and API client implementation.
- Database engine and SQLAlchemy connection handling.
- PostgreSQL and pgvector compatibility.
- Existing SQLAlchemy models and database initialization.
- Alembic availability and migration configuration.
- PDF upload, processing, retrieval, and file-storage implementation.
- Authentication, JWT security, user isolation, and workspace access control.
- CORS configuration for the production frontend domain.
- FastAPI startup, health checks, and shutdown behavior.
- Frontend production build requirements.
- Existing Render/Vercel deployment configuration, if any.

Pay particular attention to the current production behavior: production startup must not depend on automatically creating database tables if migrations are required.

Identify any missing or inconsistent configuration before changing files.

## 4. Update Environment Example Files

Update the existing `.env.example` and `backend/.env.example` as appropriate. If the repository has a separate frontend environment example, update it only if necessary.

Avoid duplicate or conflicting variable definitions.

The example files must contain descriptive placeholders, never real credentials.

### Backend environment variables

Include or retain the variables genuinely required by the existing implementation, as applicable:

- `APP_ENV`
- `APP_NAME`
- `DEBUG`
- `API_V1_STR`
- `CORS_ORIGINS`
- `DATABASE_URL`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `GEMINI_API_KEY`
- `GEMINI_GENERATION_MODEL`
- `GEMINI_EMBEDDING_MODEL`
- `EMBEDDING_DIMENSION`
- `CHUNK_SIZE_TOKENS`
- `CHUNK_OVERLAP_TOKENS`
- `RETRIEVAL_TOP_K`
- `SIMILARITY_THRESHOLD`
- `MAX_FILE_SIZE_MB`
- `MAX_DOCUMENTS_PER_WORKSPACE`
- `STORAGE_DIR`

Also add the required Supabase Storage configuration variables only if the implementation actually uses them. Determine the correct variable names from the existing code and the planned storage integration rather than inventing unused settings.

For each variable:
- Add a short comment explaining its purpose.
- Use a safe placeholder or non-sensitive example.
- State whether it is required in production or optional.
- Document the expected format where necessary.

### Database URL compatibility

Verify that the backend's SQLAlchemy async engine works with the Supabase PostgreSQL connection format.

- Use a PostgreSQL connection URL compatible with the existing `asyncpg` driver and SQLAlchemy async engine.
- Document how to obtain the correct Supabase connection string.
- Account for Supabase connection pooling and direct connections appropriately.
- Do not assume every Supabase connection URL is interchangeable.
- Do not place actual database credentials in the example file.
- Ensure URL parsing and special characters in credentials are handled safely.

### Frontend environment variables

Inspect the actual frontend API client and use its existing environment-variable naming convention where possible.

- Configure the frontend to call the deployed Render backend.
- Use a public environment variable only for values that are safe to expose in the browser, such as the backend API base URL.
- Use the correct `NEXT_PUBLIC_` prefix only when required by the frontend implementation.
- Never expose `SECRET_KEY`, database credentials, Gemini API keys, or Supabase service-role keys to the frontend.
- Document that the production frontend URL and backend CORS origins must match the actual deployed domains.

Do not create unused variables simply to fill the example file.

## 5. Supabase PostgreSQL and pgvector Readiness

Verify that the existing models, database configuration, and vector operations are compatible with Supabase PostgreSQL.

- Confirm that the required pgvector extension is handled correctly.
- Inspect vector column dimensions and embedding configuration for consistency.
- Check that all tables and indexes required by the existing application can be created through a controlled migration process.
- If Alembic is missing or incomplete, implement the minimum necessary migration setup.
- Do not automatically reset, drop, or overwrite an existing database.
- Do not run destructive database operations.
- Keep development and production database initialization behavior separate.
- Ensure production deployments have a clear and repeatable database migration procedure.

Do not assume the database is ready merely because a connection succeeds.

## 6. Persistent PDF Storage Readiness

The application must not rely on Render's ephemeral local filesystem for permanent user documents.

Inspect the existing document-storage abstraction and determine the smallest safe change required to support Supabase Storage for production.

- Preserve the existing PDF ingestion, chunking, embedding, retrieval, and citation workflows.
- Keep local filesystem storage available for development and testing if the architecture supports it.
- Make production storage selection environment-driven.
- Use private storage and appropriate access controls for user documents.
- Verify that stored document references remain valid across backend restarts and redeployments.
- Ensure document deletion and retrieval remain consistent with the existing database records.
- Never make private user PDFs publicly accessible by default.

If Supabase Storage integration requires additional implementation, complete the necessary minimal changes and document the required setup. Do not claim persistent storage is implemented unless it is actually functional.

## 7. Render Backend Deployment Readiness

Verify the correct configuration for deploying the existing FastAPI application on Render.

Determine and document:

- The correct backend root directory.
- The dependency installation command.
- The production ASGI start command.
- The correct module and application import path.
- Required Render environment variables.
- The health-check endpoint.
- The CORS configuration needed for the deployed Vercel frontend.
- How database migrations should be run safely before or during release.

Ensure the application listens on Render's provided port where applicable and uses production-safe settings.

Do not introduce a Dockerfile, render.yaml, or other deployment file unless it is actually needed by the existing project.

## 8. Vercel Frontend Deployment Readiness

Verify the current Next.js implementation and identify the correct Vercel configuration.

Determine and document:

- The correct frontend root directory.
- The production build command.
- The expected output/build behavior.
- The required frontend environment variables.
- The backend API URL configuration.
- Any existing API proxy or rewrite requirements.

Ensure the frontend uses the deployed Render backend rather than accidentally calling localhost in production.

Do not change the existing UI/UX to accomplish deployment configuration.

## 9. Security Requirements

- Production must reject the default or insecure JWT signing secret.
- Debug mode must be disabled in production.
- CORS must allow only explicitly configured trusted production origins.
- Do not expose stack traces, secrets, database URLs, or internal errors to end users.
- Ensure all document, conversation, workspace, and retrieval operations remain isolated by authenticated user and workspace permissions.
- Never trust a frontend-supplied user ID as proof of authorization.
- Do not disable authentication or authorization to make deployment easier.
- Do not introduce a hardcoded production URL.
- Keep `.gitignore` rules safe for actual environment files.
- Do not remove security protections to make the build pass.

## 10. Validation and Testing

After making changes, run the relevant checks that the local environment supports.

At minimum, attempt to verify:

- Backend imports and Python syntax.
- Existing backend automated tests.
- Frontend production build.
- Frontend lint and TypeScript checks, where available.
- Environment configuration validation using placeholders or a safe test configuration.
- SQLAlchemy async PostgreSQL connection configuration without exposing credentials.
- Migration discovery and migration-generation consistency.
- PDF storage behavior and document access-control regressions, where testable.

Do not claim a test passed unless it was actually executed successfully.

If a check cannot run because credentials or external services are unavailable, report it as NOT VERIFIED and explain the manual verification needed.

Never print environment-file contents or secrets while diagnosing failures.

## 11. Required Final Report

After completing the work, provide a concise but detailed report containing:

1. Files inspected.
2. Files modified and why.
3. Environment example variables added, updated, or removed.
4. Variables required in Supabase, Render, and Vercel.
5. Database migration readiness.
6. PDF persistent-storage readiness.
7. Security checks performed.
8. Tests actually executed and their results.
9. Remaining manual setup steps in the correct order.
10. Any production blockers that must be resolved before deployment.

Clearly distinguish between implemented, tested, and not verified.

Do not commit, push, merge, deploy, access actual `.env` files, or expose any secrets.

## Final Success Criteria

The existing ProofLens AI application must be prepared for a controlled production deployment using Supabase PostgreSQL + pgvector, Render FastAPI backend, and Vercel Next.js frontend.

Environment example files must accurately document the configuration required by the actual implementation, without containing secrets or unused variables.

All necessary changes must preserve existing functionality and frontend design. Report every remaining blocker honestly before declaring the project production-ready.
