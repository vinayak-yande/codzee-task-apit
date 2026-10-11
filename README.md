# Task API — Codzee developer evaluation

A Django 5.2 / Django REST Framework task-management API, with focused PRs
covering validation, authorization, and performance. SQLite keeps the demo
reproducible without cloud infrastructure. Python 3.12 is the tested runtime.

## Start locally

```sh
python -m venv .venv
# Windows PowerShell:
# .\.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py test
python manage.py runserver
```

Use the interactive createsuperuser command to choose your own local password.
Basic authentication is for a loopback demo; use HTTPS for any remote access.

```sh
# curl prompts for your password; do not commit credentials.
curl -u YOUR_USERNAME http://127.0.0.1:8000/api/tasks/
```

`POST /api/tasks/` accepts title, description, status, and nullable due_date.
`GET/PATCH/PUT/DELETE /api/tasks/{id}/` provide task CRUD.
Statuses are `todo`, `in_progress`, and `done`.
The authenticated user owns every newly created task; the owner field is read-only.

## Review plan

| Branch | Change | Purpose |
| --- | --- | --- |
| pr/validation | Title and due-date validation | Error handling and PATCH semantics |
| pr/ownership | Owner-only querysets for all CRUD operations | Cross-user data isolation |
| pr/performance | Pagination, list filters, joined owner lookup, composite index | Bounded responses and query efficiency |

Each branch starts from main. Open all three PRs against main before merging.
PR bodies are in `docs/pr-01.md`, `docs/pr-02.md`, and `docs/pr-03.md`.
The three changes were also merged locally to verify compatibility.

## Baseline limitations

Main is a local prototype with explicit backlog: it does not yet isolate
tasks by owner, accepts short titles and past due dates, and returns an
unpaginated task list. These are the problems addressed by the PRs.
Do not use the baseline with real user data or expose it on the internet.
Known limitations are stated openly; bugs have not been planted to manufacture
favorable review results. No Codzee feedback has yet been observed.

PRs are independent: until PR 2 is merged, PRs 1 and 3 inherit the baseline's
authorization limitation. Cross-user isolation tests apply after PR 2 or after
all changes are integrated. Evaluate feedback in this context.

PR 3 changes list responses from an array to a paginated object with `count`,
`next`, `previous`, and `results`. Page size defaults to 20 and is capped at 100.
Optional list query parameters: `status`, `search`, `ordering`, `page`, `page_size`.
Ordering accepts `created_at`, `-created_at`, `title`, or `-title`, with PK tie-breaking.
Filters apply only to the list endpoint, so detail access is not unexpectedly
affected by unrelated query parameters.

## Assessment evidence

Record review links and reproducible observations in `docs/feedback-template.md`.
The worksheet is a template, not an account of reviews that have already run.
AI assisted with the project and tests. The candidate should review and run
the code, validate Codzee suggestions, and write their own observed feedback.

## Scope and tradeoffs

No front end, signup, deployment, or external services are required for the
evaluation. Authentication uses Django users. Staff users receive no cross-user
exception after PR 2. Search uses a simple case-insensitive title match rather
than full-text search. The index supports owner/status/created-date queries,
but index usefulness depends on query shape and database; no measured latency
improvement is claimed. See `docs/evaluation-checklist.md` for review scenarios.
