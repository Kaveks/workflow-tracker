
from __future__ import annotations

from datetime import datetime
from typing import Optional

from ninja import Schema
from pydantic import EmailStr, Field

from .models import ApplicationStatus, ApplicationType


# ---------------------------------------------------------------- Output -----
class ApplicationOut(Schema):
    id: int
    tracking_number: str
    applicant_name: str
    applicant_email: str
    company_name: str
    application_type: ApplicationType
    description: str
    status: ApplicationStatus
    reviewer_comment: str
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]
    reviewed_at: Optional[datetime]


# ---------------------------------------------------------------- Inputs -----
class ApplicationDraftIn(Schema):
    """Payload for creating or updating a draft application."""

    applicant_name: str = Field(..., min_length=1, max_length=200)
    applicant_email: EmailStr
    company_name: str = Field(..., min_length=1, max_length=200)
    application_type: ApplicationType
    description: str = Field(default="", max_length=5000)


class ReviewerDecisionIn(Schema):
    """Reviewer's final action on an Under-Review application.

    The service layer enforces that `comment` is non-empty when
    decision is NEED_MORE_INFORMATION or REJECTED.
    """

    decision: ApplicationStatus
    comment: str = Field(default="", max_length=5000)


# ----------------------------------------------------------------- Error -----
class ErrorOut(Schema):
    detail: str