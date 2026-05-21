from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html

from .models import Application, ApplicationStatus



_STATUS_COLOURS: dict[str, str] = {
    ApplicationStatus.DRAFT: "#6b7280",                  # slate-500
    ApplicationStatus.SUBMITTED: "#2563eb",              # blue-600
    ApplicationStatus.UNDER_REVIEW: "#b45309",           # amber-700
    ApplicationStatus.NEED_MORE_INFORMATION: "#c2410c",  # orange-700
    ApplicationStatus.APPROVED: "#15803d",               # green-700
    ApplicationStatus.REJECTED: "#b91c1c",               # red-700
}


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    # List view
    list_display = (
        "tracking_number",
        "applicant_name",
        "company_name",
        "application_type",
        "status_badge",
        "created_at",
        "submitted_at",
        "reviewed_at",
    )
    list_display_links = ("tracking_number", "applicant_name")
    list_filter = ("status", "application_type", "created_at")
    search_fields = (
        "tracking_number",
        "applicant_name",
        "applicant_email",
        "company_name",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_per_page = 25

    # Detail view
    fieldsets = (
        (
            "Identification",
            {"fields": ("tracking_number", "status")},
        ),
        (
            "Applicant",
            {
                "fields": (
                    "applicant_name",
                    "applicant_email",
                    "company_name",
                )
            },
        ),
        (
            "Application",
            {"fields": ("application_type", "description")},
        ),
        (
            "Review",
            {"fields": ("reviewer_comment",)},
        ),
        (
            "Timestamps",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                    "submitted_at",
                    "reviewed_at",
                ),
            },
        ),
    )

    # Audit/system fields are never user-editable from the admin —
    # they are set by the service layer when transitions happen.
    readonly_fields = (
        "tracking_number",
        "created_at",
        "updated_at",
        "submitted_at",
        "reviewed_at",
    )

    # helper method to render the status with a coloured badge in the list view
    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj: Application) -> str:
        """Render the status as a coloured pill in the changelist."""
        colour = _STATUS_COLOURS.get(obj.status, "#374151")
        return format_html(
            '<span style="display:inline-block;padding:2px 8px;'
            "border-radius:9999px;font-size:11px;font-weight:600;"
            'color:#fff;background:{};">{}</span>',
            colour,
            obj.get_status_display(),
        )