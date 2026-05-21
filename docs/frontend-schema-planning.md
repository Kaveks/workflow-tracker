# Frontend schema planning

This document is the single source of truth for backend planning.
Schema evolves from the frontend's requirements; the backend is shaped
to match what the UI needs, not the other way around.

## Conventions

- All entities use a server-assigned integer `id`.
- Timestamps are ISO-8601 strings in UTC and are server-generated.
- Enum values on the wire are snake_case so they can be used directly
  as discriminants and dictionary keys.
- All mutating endpoints return the full updated resource so the
  client does not need a follow-up `GET`.

---

## Entity: Application

The only domain entity in v1.

### Fields

| Field              | Type                      | Required          | Notes                                                            |
| ------------------ | ------------------------- | ----------------- | ---------------------------------------------------------------- |
| `id`               | `integer`                 | server-generated  | Primary key.                                                     |
| `tracking_number`  | `string`                  | server-generated  | Short, human-readable. Pattern `APP-XXXXXXXX`. Unique.           |
| `applicant_name`   | `string` (1–200)          | yes               |                                                                  |
| `applicant_email`  | `string` (RFC 5322 email) | yes               |                                                                  |
| `company_name`     | `string` (1–200)          | yes               |                                                                  |
| `application_type` | enum (see below)          | yes               | Fixed set; surfaced as a `Select` in the UI.                     |
| `description`      | `string` (0–5000)         | no                | Free text from the applicant.                                    |
| `status`           | enum (see below)          | server-controlled | Mutated only via workflow endpoints, never the draft endpoints.  |
| `reviewer_comment` | `string` (0–5000)         | conditional       | Required when decision is `need_more_information` or `rejected`. |
| `created_at`       | `datetime`                | server-generated  |                                                                  |
| `updated_at`       | `datetime`                | server-generated  | Touched on any change.                                           |
| `submitted_at`     | `datetime \| null`        | server-generated  | Set when status transitions to `submitted`.                      |
| `reviewed_at`      | `datetime \| null`        | server-generated  | Set when the reviewer records a decision.                        |

### `application_type`

`recordation` · `renewal` · `change_of_ownership` · `change_of_name` · `discontinuation`

### `status`

`draft` · `submitted` · `under_review` · `need_more_information` · `approved` · `rejected`

### Validation rules

- `applicant_email` must be a valid email.
- `applicant_name`, `company_name`: non-empty after trimming.
- `application_type` must be a known enum value.
- `description`, `reviewer_comment`: max 5000 characters each.
- Comment is required (after trimming) for `need_more_information` and `rejected`.

### Relationships

None in v1. A future iteration will likely add:

- `Reviewer` (user) with FK from `Application.reviewed_by`
- `Applicant` (user) with FK from `Application.created_by`
- `Attachment` (many-to-one to `Application`) for supporting documents

These were deferred because the brief did not require authentication.

---

## State machine

```
   draft
     │  submit
     ▼
 submitted
     │  start_review
     ▼
 under_review ──► approved
     │           │
     ├──────────► rejected             (comment required)
     │
     └──────────► need_more_information (comment required)
                       │  edit + submit
                       ▼
                   submitted
```

Transition rules — enforced on the backend in `applications/services.py`:

| Action          | Allowed from                     | Effect                                                                                         |
| --------------- | -------------------------------- | ---------------------------------------------------------------------------------------------- |
| Edit            | `draft`, `need_more_information` | Updates editable fields; no status change.                                                     |
| Submit          | `draft`, `need_more_information` | → `submitted`; sets `submitted_at`.                                                            |
| Start review    | `submitted`                      | → `under_review`.                                                                              |
| Record decision | `under_review`                   | → `approved` \| `rejected` \| `need_more_information`. Sets `reviewed_at`, `reviewer_comment`. |

The frontend mirrors this in `features/applications/actions.ts` purely
to choose which buttons to render. The backend is always authoritative;
attempts to violate a rule return HTTP 409 with a `detail` message that
the UI surfaces verbatim.

---

## API endpoints

Base path: `/api`

| Method | Path                               | Body                 | Response               | Purpose                 |
| ------ | ---------------------------------- | -------------------- | ---------------------- | ----------------------- |
| `GET`  | `/applications/?status=&search=`   | —                    | `Application[]`        | List, optional filters. |
| `POST` | `/applications/`                   | `ApplicationDraftIn` | `201 Application`      | Create draft.           |
| `GET`  | `/applications/{id}/`              | —                    | `Application`          | Detail.                 |
| `PUT`  | `/applications/{id}/`              | `ApplicationDraftIn` | `Application` \| `409` | Update draft.           |
| `POST` | `/applications/{id}/submit/`       | —                    | `Application` \| `409` | Submit.                 |
| `POST` | `/applications/{id}/start-review/` | —                    | `Application` \| `409` | Start review.           |
| `POST` | `/applications/{id}/decision/`     | `ReviewerDecisionIn` | `Application` \| `409` | Record decision.        |

### Error shape

```json
{ "detail": "Only draft applications can be edited." }
```

---

## Scalability considerations

- **Indexes**: `status` and `created_at` are indexed because they drive
  the list view's filter and sort. Adding text search (e.g. PostgreSQL
  `pg_trgm` on `tracking_number`, `applicant_name`, `company_name`) is
  the next logical step.
- **Pagination**: list returns the full set in v1 because the brief
  doesn't require pagination. The endpoint accepts query parameters
  already; adding `?page=&page_size=` will be a non-breaking change.
- **Audit trail**: `submitted_at` and `reviewed_at` give a partial
  history. A dedicated `ApplicationEvent` table would be needed once
  the workflow expands beyond the current six states.
- **Database**: SQLite is fine for the assignment; switching to
  PostgreSQL is a `DATABASES` setting change plus a new migration.
  No application code needs to change.

---

## Future schema additions (not in v1)

- Authentication: `User`, role-based permissions for reviewer actions.
- `Attachment` model for supporting documents (FK to `Application`).
- `ApplicationEvent` audit log: who did what, when.
- Pagination metadata on list responses (`{ items, total, page, page_size }`).
- Tag/category model for finer-grained workflow segmentation.

When any of these are added, this document is updated **first** and
the backend is changed to match.
