
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from .models import Application, ApplicationStatus


class WorkflowError(Exception):
    """Raised when a workflow rule is violated.

    The API layer maps this to an HTTP 409 with the message body.
    """


# Statuses from which a user can edit the draft fields of an application.
EDITABLE_STATUSES: frozenset[str] = frozenset(
    {ApplicationStatus.DRAFT, ApplicationStatus.NEED_MORE_INFORMATION}
)

# Statuses from which a user can submit (or resubmit) an application.
SUBMITTABLE_STATUSES: frozenset[str] = frozenset(
    {ApplicationStatus.DRAFT, ApplicationStatus.NEED_MORE_INFORMATION}
)

# Decisions that require a comment from the reviewer.
COMMENT_REQUIRED_DECISIONS: frozenset[str] = frozenset(
    {ApplicationStatus.NEED_MORE_INFORMATION, ApplicationStatus.REJECTED}
)

# Valid decisions a reviewer can record from "Under Review".
VALID_REVIEWER_DECISIONS: frozenset[str] = frozenset(
    {
        ApplicationStatus.APPROVED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.NEED_MORE_INFORMATION,
    }
)


# ----------------------------------------------------------- Mutations ------
@transaction.atomic
def create_draft(*, data: dict) -> Application:
    """Create a new application in Draft status."""
    return Application.objects.create(status=ApplicationStatus.DRAFT, **data)


@transaction.atomic
def update_draft(*, application: Application, data: dict) -> Application:
    """Update editable fields. Allowed in Draft or Need More Information."""
    if application.status not in EDITABLE_STATUSES:
        raise WorkflowError(
            f"Cannot edit application in status '{application.get_status_display()}'."
        )
    for field, value in data.items():
        setattr(application, field, value)
    application.save()
    return application


@transaction.atomic
def submit_application(*, application: Application) -> Application:
    """Move an application from Draft (or Need More Info) to Submitted."""
    if application.status not in SUBMITTABLE_STATUSES:
        raise WorkflowError(
            f"Cannot submit application in status '{application.get_status_display()}'."
        )
    application.status = ApplicationStatus.SUBMITTED
    application.submitted_at = timezone.now()
    application.save(update_fields=["status", "submitted_at", "updated_at"])
    return application


@transaction.atomic
def start_review(*, application: Application) -> Application:
    """Move a Submitted application into Under Review."""
    if application.status != ApplicationStatus.SUBMITTED:
        raise WorkflowError(
            "Only submitted applications can be moved to Under Review."
        )
    application.status = ApplicationStatus.UNDER_REVIEW
    application.save(update_fields=["status", "updated_at"])
    return application


@transaction.atomic
def record_decision(
    *, application: Application, decision: str, comment: str
) -> Application:
    """Apply a reviewer's final decision to an Under-Review application."""
    if application.status != ApplicationStatus.UNDER_REVIEW:
        raise WorkflowError(
            "Only applications Under Review can receive a reviewer decision."
        )
    if decision not in VALID_REVIEWER_DECISIONS:
        raise WorkflowError(
            f"'{decision}' is not a valid reviewer decision."
        )

    normalised_comment = (comment or "").strip()
    if decision in COMMENT_REQUIRED_DECISIONS and not normalised_comment:
        raise WorkflowError(
            "A reviewer comment is required for this decision."
        )

    application.status = decision
    application.reviewer_comment = normalised_comment
    application.reviewed_at = timezone.now()
    application.save(
        update_fields=["status", "reviewer_comment", "reviewed_at", "updated_at"]
    )
    return application