from django import forms
from .models import Tag, Prompt, Run, validate_not_blank


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["title", "notes"]

    def clean_title(self):
        title = self.cleaned_data.get("title", "")
        validate_not_blank(title)
        if len(title) > 100:
            raise forms.ValidationError("标签名称不能超过100个字符")
        return title

    def clean_notes(self):
        notes = self.cleaned_data.get("notes", "")
        validate_not_blank(notes)
        return notes


class PromptForm(forms.ModelForm):
    class Meta:
        model = Prompt
        fields = ["title", "content", "notes", "tags", "version", "rating"]
        widgets = {
            "tags": forms.CheckboxSelectMultiple(),
        }

    def clean_title(self):
        title = self.cleaned_data.get("title", "")
        validate_not_blank(title)
        if len(title) > 100:
            raise forms.ValidationError("提示词名称不能超过100个字符")
        return title

    def clean_content(self):
        content = self.cleaned_data.get("content", "")
        validate_not_blank(content)
        return content

    def clean_notes(self):
        notes = self.cleaned_data.get("notes", "")
        validate_not_blank(notes)
        return notes


class RunForm(forms.ModelForm):
    class Meta:
        model = Run
        fields = ["model", "tokens", "response_time"]
