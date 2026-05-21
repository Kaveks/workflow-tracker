"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from __future__ import annotations

from django.contrib import admin
from django.urls import path,include
from django.http import JsonResponse
from django.conf.urls.static import static
from django.conf import settings
from ninja import NinjaAPI

from applications.api import router as applications_router

applications_apis = NinjaAPI(
    title="Workflow Tracker API",
    version="1.0.0",
    description="Application workflow tracking service.",
)

applications_apis.add_router("/applications", applications_router, tags=["applications"])



def healthcheck(_request):
    return JsonResponse({"status": "ok"})

# get docs
#http://127.0.0.1:8000/api/v1/openapi.json
#http://127.0.0.1:8000/api/v1/docs
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", applications_apis.urls),
    path("health/", healthcheck),
]

# STATIC + MEDIA (DEV ONLY)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)