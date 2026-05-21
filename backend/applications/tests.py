from django.test import TestCase

# Create your tests here.
"""Tests covering the workflow state machine.

These verify the rules called out in the assignment brief: only certain
statuses can be edited, submitted, reviewed, etc., and that a comment
is required for Need More Information / Rejected decisions.
"""
from __future__ import annotations

from applications import services
from applications.models import Application, ApplicationStatus, ApplicationType


def _make_draft(**overrides) -> Application:
    data = {
        "applicant_name": "Ada Lovelace",
        "applicant_email": "ada@example.com",
        "company_name": "Analytical Engines Ltd",
        "application_type": ApplicationType.RECORDATION,
        "description": "Initial filing.",
    }
    data.update(overrides)
    return services.create_draft(data=data)


class WorkflowTransitionTests(TestCase):
    def test_create_draft_starts_in_draft_status(self):
        application = _make_draft()
        self.assertEqual(application.status, ApplicationStatus.DRAFT)
        self.assertTrue(application.tracking_number.startswith("APP-"))

    def test_can_edit_a_draft(self):
        application = _make_draft()
        services.update_draft(
            application=application,
            data={"description": "Updated copy"},
        )
        application.refresh_from_db()
        self.assertEqual(application.description, "Updated copy")

    def test_cannot_edit_an_approved_application(self):
        application = _make_draft()
        services.submit_application(application=application)
        services.start_review(application=application)
        services.record_decision(
            application=application,
            decision=ApplicationStatus.APPROVED,
            comment="",
        )
        with self.assertRaises(services.WorkflowError):
            services.update_draft(
                application=application,
                data={"description": "tampering"},
            )

    def test_submit_only_from_draft_or_need_more_info(self):
        application = _make_draft()
        services.submit_application(application=application)
        # Already submitted, cannot resubmit from this state.
        with self.assertRaises(services.WorkflowError):
            services.submit_application(application=application)

    def test_start_review_only_from_submitted(self):
        application = _make_draft()
        with self.assertRaises(services.WorkflowError):
            services.start_review(application=application)

    def test_decision_requires_under_review(self):
        application = _make_draft()
        with self.assertRaises(services.WorkflowError):
            services.record_decision(
                application=application,
                decision=ApplicationStatus.APPROVED,
                comment="",
            )

    def test_rejection_requires_comment(self):
        application = _make_draft()
        services.submit_application(application=application)
        services.start_review(application=application)
        with self.assertRaises(services.WorkflowError):
            services.record_decision(
                application=application,
                decision=ApplicationStatus.REJECTED,
                comment="   ",  # whitespace-only is treated as missing
            )

    def test_need_more_info_allows_resubmission(self):
        application = _make_draft()
        services.submit_application(application=application)
        services.start_review(application=application)
        services.record_decision(
            application=application,
            decision=ApplicationStatus.NEED_MORE_INFORMATION,
            comment="Please attach supporting documents.",
        )
        # Edit and resubmit
        services.update_draft(
            application=application,
            data={"description": "Now with documents."},
        )
        services.submit_application(application=application)
        application.refresh_from_db()
        self.assertEqual(application.status, ApplicationStatus.SUBMITTED)