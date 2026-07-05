import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Tag, Prompt, Run
from .forms import TagForm, PromptForm, RunForm


# ── Helpers ────────────────────────────────────────

def _json_success(data=None, status=200):
    return JsonResponse({"success": True, "data": data}, status=status)


def _json_error(error, status=400):
    return JsonResponse({"success": False, "error": error}, status=status)


def _tag_dict(tag):
    return {
        "id": tag.id, "title": tag.title, "notes": tag.notes,
        "createdAt": tag.created_at.isoformat(), "updatedAt": tag.updated_at.isoformat(),
    }


def _prompt_dict(prompt):
    return {
        "id": prompt.id, "title": prompt.title, "content": prompt.content,
        "notes": prompt.notes, "version": prompt.version or None, "rating": prompt.rating,
        "tags": [_tag_dict(t) for t in prompt.tags.all()],
        "runs": [{"id": r.id, "model": r.model, "tokens": r.tokens,
                   "responseTime": r.response_time, "createdAt": r.created_at.isoformat()}
                  for r in prompt.runs.all()],
        "createdAt": prompt.created_at.isoformat(), "updatedAt": prompt.updated_at.isoformat(),
    }


# ── Template views ─────────────────────────────────

def prompt_list(request):
    prompts = Prompt.objects.prefetch_related("tags").all()
    return render(request, "prompts/prompt_list.html", {"prompts": prompts})


def prompt_detail(request, pk):
    prompt = get_object_or_404(Prompt.objects.prefetch_related("tags", "runs"), pk=pk)
    return render(request, "prompts/prompt_detail.html", {"prompt": prompt, "run_form": RunForm()})


def prompt_create(request):
    if request.method == "POST":
        form = PromptForm(request.POST)
        if form.is_valid():
            prompt = form.save()
            return redirect("prompt_detail", pk=prompt.pk)
    else:
        form = PromptForm()
    return render(request, "prompts/prompt_form.html", {"form": form, "tags": Tag.objects.all(), "is_edit": False})


def prompt_edit(request, pk):
    prompt = get_object_or_404(Prompt, pk=pk)
    if request.method == "POST":
        form = PromptForm(request.POST, instance=prompt)
        if form.is_valid():
            form.save()
            return redirect("prompt_detail", pk=prompt.pk)
    else:
        form = PromptForm(instance=prompt)
    return render(request, "prompts/prompt_form.html", {"form": form, "tags": Tag.objects.all(), "is_edit": True, "prompt": prompt})


def prompt_delete(request, pk):
    prompt = get_object_or_404(Prompt, pk=pk)
    if request.method == "POST":
        prompt.delete()
        return redirect("prompt_list")
    return render(request, "prompts/prompt_confirm_delete.html", {"prompt": prompt})


def tag_list(request):
    return render(request, "prompts/tag_list.html", {"tags": Tag.objects.all()})


def tag_detail(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    prompts = tag.prompts.prefetch_related("tags").all()
    return render(request, "prompts/tag_detail.html", {"tag": tag, "prompts": prompts})


def tag_create(request):
    if request.method == "POST":
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save()
            return redirect("tag_list")
    else:
        form = TagForm()
    return render(request, "prompts/tag_form.html", {"form": form, "is_edit": False})


def tag_edit(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == "POST":
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            return redirect("tag_detail", pk=tag.pk)
    else:
        form = TagForm(instance=tag)
    return render(request, "prompts/tag_form.html", {"form": form, "is_edit": True, "tag": tag})


def tag_delete(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == "POST":
        tag.delete()
        return redirect("tag_list")
    return render(request, "prompts/tag_confirm_delete.html", {"tag": tag})


def tag_edit_notes(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == "POST":
        tag.notes = request.POST.get("notes", tag.notes)
        tag.save()
    return redirect("tag_detail", pk=tag.pk)


def run_add(request, prompt_pk):
    prompt = get_object_or_404(Prompt, pk=prompt_pk)
    if request.method == "POST":
        form = RunForm(request.POST)
        if form.is_valid():
            run = form.save(commit=False)
            run.prompt = prompt
            run.save()
    return redirect("prompt_detail", pk=prompt.pk)


def run_delete(request, prompt_pk, run_pk):
    run = get_object_or_404(Run, pk=run_pk, prompt_id=prompt_pk)
    if request.method == "POST":
        run.delete()
    return redirect("prompt_detail", pk=prompt_pk)


# ── JSON API ───────────────────────────────────────

@csrf_exempt
def api_tags(request):
    if request.method == "GET":
        return _json_success([_tag_dict(t) for t in Tag.objects.all()])
    elif request.method == "POST":
        try: data = json.loads(request.body)
        except json.JSONDecodeError: return _json_error("请求格式错误")
        form = TagForm(data)
        if form.is_valid():
            tag = form.save()
            return _json_success(_tag_dict(tag), status=201)
        return _json_error("; ".join(f"{k}: {v[0]}" for k, v in form.errors.items()))


@csrf_exempt
def api_tag_detail(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == "GET":
        return _json_success(_tag_dict(tag))
    elif request.method == "PUT":
        try: data = json.loads(request.body)
        except json.JSONDecodeError: return _json_error("请求格式错误")
        for field, value in data.items():
            if hasattr(tag, field):
                setattr(tag, field, value)
        try:
            tag.full_clean()
            tag.save()
            return _json_success(_tag_dict(tag))
        except Exception as e:
            return _json_error(str(e))
    elif request.method == "DELETE":
        tag.delete()
        return _json_success({"message": "删除成功"})


@csrf_exempt
def api_prompts(request):
    if request.method == "GET":
        prompts = Prompt.objects.prefetch_related("tags", "runs").all()
        return _json_success([_prompt_dict(p) for p in prompts])
    elif request.method == "POST":
        try: data = json.loads(request.body)
        except json.JSONDecodeError: return _json_error("请求格式错误")
        form = PromptForm(data)
        if form.is_valid():
            prompt = form.save()
            return _json_success(_prompt_dict(prompt), status=201)
        return _json_error("; ".join(f"{k}: {v[0]}" for k, v in form.errors.items()))


@csrf_exempt
def api_prompt_detail(request, pk):
    prompt = get_object_or_404(Prompt.objects.prefetch_related("tags", "runs"), pk=pk)
    if request.method == "GET":
        return _json_success(_prompt_dict(prompt))
    elif request.method == "PUT":
        try: data = json.loads(request.body)
        except json.JSONDecodeError: return _json_error("请求格式错误")
        runs_data = data.pop("runs", None)
        tags_data = data.pop("tags", None)
        for field, value in data.items():
            if hasattr(prompt, field):
                setattr(prompt, field, value)
        try:
            prompt.full_clean()
            prompt.save()
            if tags_data is not None:
                prompt.tags.set(tags_data)
            if runs_data is not None:
                prompt.runs.all().delete()
                for r in runs_data:
                    Run.objects.create(prompt=prompt, model=r.get("model", ""),
                                       tokens=r.get("tokens", 0), response_time=r.get("responseTime", 0))
            return _json_success(_prompt_dict(prompt))
        except Exception as e:
            return _json_error(str(e))
    elif request.method == "DELETE":
        prompt.delete()
        return _json_success({"message": "删除成功"})
