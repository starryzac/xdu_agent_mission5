from django.db import models
from django.core.exceptions import ValidationError


def validate_not_blank(value):
    if not value or not value.strip():
        raise ValidationError("此字段不能为空或全为空格")


class Tag(models.Model):
    title = models.CharField(max_length=100, validators=[validate_not_blank])
    notes = models.TextField(validators=[validate_not_blank])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class Prompt(models.Model):
    title = models.CharField(max_length=100, validators=[validate_not_blank])
    content = models.TextField(validators=[validate_not_blank])
    notes = models.TextField(validators=[validate_not_blank])
    tags = models.ManyToManyField(Tag, blank=True, related_name="prompts")
    version = models.CharField(max_length=50, blank=True, default="")
    rating = models.IntegerField(null=True, blank=True, choices=[(i, str(i)) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class Run(models.Model):
    prompt = models.ForeignKey(Prompt, on_delete=models.CASCADE, related_name="runs")
    model = models.CharField(max_length=100)
    tokens = models.IntegerField(default=0)
    response_time = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
