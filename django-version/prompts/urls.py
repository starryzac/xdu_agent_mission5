from django.urls import path
from . import views

urlpatterns = [
    # ── Template routes ──────────────────────────
    path("", views.prompt_list, name="prompt_list"),
    path("prompts/<int:pk>/", views.prompt_detail, name="prompt_detail"),
    path("prompts/new/", views.prompt_create, name="prompt_create"),
    path("prompts/<int:pk>/edit/", views.prompt_edit, name="prompt_edit"),
    path("prompts/<int:pk>/delete/", views.prompt_delete, name="prompt_delete"),
    path("prompts/<int:pk>/runs/add/", views.run_add, name="run_add"),
    path("prompts/<int:pk>/runs/<int:run_pk>/delete/", views.run_delete, name="run_delete"),
    path("tags/", views.tag_list, name="tag_list"),
    path("tags/new/", views.tag_create, name="tag_create"),
    path("tags/<int:pk>/", views.tag_detail, name="tag_detail"),
    path("tags/<int:pk>/edit/", views.tag_edit, name="tag_edit"),
    path("tags/<int:pk>/delete/", views.tag_delete, name="tag_delete"),
    path("tags/<int:pk>/notes/", views.tag_edit_notes, name="tag_edit_notes"),

    # ── JSON API routes ──────────────────────────
    path("api/tags/", views.api_tags, name="api_tags"),
    path("api/tags/<int:pk>/", views.api_tag_detail, name="api_tag_detail"),
    path("api/prompts/", views.api_prompts, name="api_prompts"),
    path("api/prompts/<int:pk>/", views.api_prompt_detail, name="api_prompt_detail"),
]
