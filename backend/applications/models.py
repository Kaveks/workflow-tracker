from __future__ import annotations

import secrets
import string
from django.db import models
from django.utils import timezone

# Create your models here.




def _generate_tracking_number() -> str:
    """Generate a short, human-friendly tracking number.

    Format: APP-XXXXXXXX (8 uppercase alphanumerics).
    Uses `secrets` to avoid predictable IDs; a unique-index handles collisions.
    """
    alphabet = string.ascii_uppercase + string.digits
    suffix = "".join(secrets.choice(alphabet) for _ in range(8))
    return f"APP-{suffix}"


class ApplicationType(models.TextChoices):
    RECORDATION = "recordation", "Recordation"
    RENEWAL = "renewal", "Renewal"
    CHANGE_OF_OWNERSHIP = "change_of_ownership", "Change of Ownership"
    CHANGE_OF_NAME = "change_of_name", "Change of Name"
    DISCONTINUATION = "discontinuation", "Discontinuation"


class ApplicationStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    SUBMITTED = "submitted", "Submitted"
    UNDER_REVIEW = "under_review", "Under Review"
    NEED_MORE_INFORMATION = "need_more_information", "Need More Information"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class Application(models.Model):
    """An application moving through the workflow.

    State machine is enforced in `applications.services`, not in this model,
    to keep persistence and business rules cleanly separated.
    """

    tracking_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        default=_generate_tracking_number,
    )
    applicant_name = models.CharField(max_length=200)
    applicant_email = models.EmailField()
    company_name = models.CharField(max_length=200)
    application_type = models.CharField(
        max_length=32,
        choices=ApplicationType.choices,
    )
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=32,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT,
    )
    reviewer_comment = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.tracking_number} ({self.get_status_display()})"