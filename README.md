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

Three public PRs are open against main: [validation](https://github.com/vinayak-yande/codzee-task-apit/pull/1),
[ownership](https://github.com/vinayak-yande/codzee-task-apit/pull/2), and
[performance](https://github.com/vinayak-yande/codzee-task-apit/pull/3).
They initially started independently; PR 3 now includes PR 2 as a security dependency.
PR bodies are in `docs/pr-01.md`, `docs/pr-02.md`, and `docs/pr-03.md`.
The three current changes were combined locally: all 42 tests pass, Django checks
pass, and no migration drift is detected. GitHub CI passes on each PR head.

## Baseline limitations

Main is a local prototype with explicit backlog: it does not yet isolate
tasks by owner, accepts short titles and past due dates, and returns an
unpaginated task list. These are the problems addressed by the PRs.
Do not use the baseline with real user data or expose it on the internet.
Known limitations are stated openly; bugs have not been planted to manufacture
favorable review results. Codzee reviews are visible on all three PRs.

PR 1 inherits the baseline authorization limitation until integrated with PR 2.
PR 3 includes PR 2's owner-isolation fix before exposing search. Main remains the
prototype baseline so the three open PRs retain their reviewable changes. Evaluate feedback in this context.

PR 3 changes list responses from an array to a paginated object with `count`,
`next`, `previous`, and `results`. Page size defaults to 20 and is capped at 100.
Optional list query parameters: `status`, `search`, `ordering`, `page`, `page_size`.
Ordering accepts `created_at`, `-created_at`, `title`, or `-title`, with PK tie-breaking.
Filters apply only to the list endpoint, so detail access is not unexpectedly
affected by unrelated query parameters.

## Assessment evidence

Codzee found an unchanged-overdue-date update bug in PR 1; PUT and PATCH
regressions reproduced it before the fix and pass afterwards. Its PR 3 warning
about inherited cross-user search led to including PR 2 and filtered isolation
tests. An ordering-coverage suggestion led to explicit descending-title and
ascending-date tests. PR 2 received a no-issues review. The dashboard displayed
clean incremental re-reviews for the updated PR 1 and PR 3 commits. Original
review comments remain accessible for evaluation.

`docs/feedback-template.md` remains a blank worksheet. AI assisted with project
implementation and tests; feedback should be checked against the actual reviews.

## Scope and tradeoffs

No front end, signup, deployment, or external services are required for the
evaluation. Authentication uses Django users. Staff users receive no cross-user
exception after PR 2. Search uses a simple case-insensitive title match rather
than full-text search. The index supports owner/status/created-date queries,
but index usefulness depends on query shape and database; no measured latency
improvement is claimed. See `docs/evaluation-checklist.md` for review scenarios.
