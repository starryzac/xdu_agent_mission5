from django.contrib import admin
from .models import Tag, Prompt, Run


class RunInline(admin.TabularInline):
    model = Run
    extra = 0


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["title", "notes", "created_at", "updated_at"]
    search_fields = ["title"]


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    list_display = ["title", "version", "rating", "created_at", "updated_at"]
    search_fields = ["title", "content"]
    filter_horizontal = ["tags"]
    inlines = [RunInline]
