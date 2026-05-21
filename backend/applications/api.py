
from __future__ import annotations

from typing import Optional

from django.shortcuts import get_object_or_404
from ninja import Query, Router
from django.db.models import Q
from . import services
from .models import Application, ApplicationStatus
from .schemas import (
    ApplicationDraftIn,
    ApplicationOut,
    ErrorOut,
    ReviewerDecisionIn,
)

router = Router()


# List
@router.get("/", response=list[ApplicationOut])
def list_applications(
    request,
    status: Optional[ApplicationStatus] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=200),
):
    """List all applications, optionally filtered by status or search term."""
    queryset = Application.objects.all()
    if status:
        queryset = queryset.filter(status=status)
    if search:
        term = search.strip()
        if term:
            queryset = queryset.filter(
                Q(tracking_number__icontains=term) |
                Q(applicant_name__icontains=term) |
                Q(company_name__icontains=term)
            )
    return list(queryset.distinct())


# Detail 
@router.get("/{application_id}/", response=ApplicationOut)
def get_application(request, application_id: int):
    """Get a single application by ID."""
    return get_object_or_404(Application, id=application_id)


# Create 
@router.post("/", response={201: ApplicationOut, 422: ErrorOut})
def create_application(request, payload: ApplicationDraftIn):
    """Create a new application draft."""
    application = services.create_draft(data=payload.model_dump())
    return 201, application


# Update 
@router.put(
    "/{application_id}/",
    response={200: ApplicationOut, 409: ErrorOut},
)
def update_application(
    request, application_id: int, payload: ApplicationDraftIn
):
    """Update an existing application draft. Only allowed if application is still a draft."""
    application = get_object_or_404(Application, id=application_id)
    try:
        application = services.update_draft(
            application=application, data=payload.model_dump(exclude_unset=True)
        )
    except services.WorkflowError as exc:
        return 409, {"detail": str(exc)}
    return 200, application


# Submit
@router.post(
    "/{application_id}/submit/",
    response={200: ApplicationOut, 409: ErrorOut},
)
def submit_application(request, application_id: int):
    application = get_object_or_404(Application, id=application_id)
    """Submit an application for review."""
    try:
        application = services.submit_application(application=application)
    except services.WorkflowError as exc:
        return 409, {"detail": str(exc)}
    return 200, application


# Start review 
@router.post(
    "/{application_id}/start-review/",
    response={200: ApplicationOut, 409: ErrorOut},
)
def start_review(request, application_id: int):
    """Start the review process for an application."""
    application = get_object_or_404(Application, id=application_id)
    try:
        application = services.start_review(application=application)
    except services.WorkflowError as exc:
        return 409, {"detail": str(exc)}
    return 200, application


# Decision 
@router.post(
    "/{application_id}/decision/",
    response={200: ApplicationOut, 409: ErrorOut},
)
def record_decision(
    request, application_id: int, payload: ReviewerDecisionIn
):
    """Record a reviewer's decision for an application."""
    application = get_object_or_404(Application, id=application_id)
    try:
        application = services.record_decision(
            application=application,
            decision=payload.decision,
            comment=payload.comment,
        )
    except services.WorkflowError as exc:
        return 409, {"detail": str(exc)}
    return 200, application