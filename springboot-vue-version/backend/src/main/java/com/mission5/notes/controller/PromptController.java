package com.mission5.notes.controller;

import com.mission5.notes.dto.ApiResponse;
import com.mission5.notes.entity.Prompt;
import com.mission5.notes.entity.Run;
import com.mission5.notes.entity.Tag;
import com.mission5.notes.repository.PromptRepository;
import com.mission5.notes.repository.TagRepository;
import jakarta.validation.Valid;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.*;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/prompts")
public class PromptController {

    private final PromptRepository repo;
    private final TagRepository tagRepo;

    public PromptController(PromptRepository repo, TagRepository tagRepo) {
        this.repo = repo; this.tagRepo = tagRepo;
    }

    @GetMapping
    public ApiResponse<List<Prompt>> list() {
        return ApiResponse.success(repo.findAll(Sort.by(Sort.Direction.DESC, "updatedAt")));
    }

    @GetMapping("/{id}")
    public ApiResponse<Prompt> get(@PathVariable Long id) {
        return repo.findById(id)
            .map(ApiResponse::success)
            .orElseGet(() -> ApiResponse.error("提示词不存在"));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ApiResponse<Prompt> create(@Valid @RequestBody Map<String, Object> body) {
        Prompt prompt = new Prompt();
        applyFields(prompt, body);
        return ApiResponse.success(repo.save(prompt));
    }

    @PutMapping("/{id}")
    public ApiResponse<Prompt> update(@PathVariable Long id, @RequestBody Map<String, Object> body) {
        return repo.findById(id).map(prompt -> {
            applyFields(prompt, body);
            return ApiResponse.success(repo.save(prompt));
        }).orElseGet(() -> ApiResponse.error("提示词不存在"));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Map<String, String>> delete(@PathVariable Long id) {
        if (!repo.existsById(id)) return ApiResponse.error("提示词不存在");
        repo.deleteById(id);
        return ApiResponse.success(Map.of("message", "删除成功"));
    }

    @SuppressWarnings("unchecked")
    private void applyFields(Prompt prompt, Map<String, Object> body) {
        if (body.containsKey("title")) prompt.setTitle((String) body.get("title"));
        if (body.containsKey("content")) prompt.setContent((String) body.get("content"));
        if (body.containsKey("notes")) prompt.setNotes((String) body.get("notes"));
        if (body.containsKey("version")) prompt.setVersion((String) body.get("version"));
        if (body.containsKey("rating")) prompt.setRating(body.get("rating") != null ? ((Number) body.get("rating")).intValue() : null);

        // Tags
        if (body.containsKey("tags")) {
            List<Number> tagIds = (List<Number>) body.get("tags");
            Set<Tag> tags = tagIds.stream()
                .map(n -> tagRepo.findById(n.longValue()))
                .filter(Optional::isPresent)
                .map(Optional::get)
                .collect(Collectors.toSet());
            prompt.setTags(tags);
        }

        // Runs
        if (body.containsKey("runs")) {
            prompt.getRuns().clear();
            List<Map<String, Object>> runsData = (List<Map<String, Object>>) body.get("runs");
            for (Map<String, Object> rd : runsData) {
                Run run = new Run();
                run.setPrompt(prompt);
                run.setModel((String) rd.get("model"));
                run.setTokens(rd.get("tokens") != null ? ((Number) rd.get("tokens")).intValue() : 0);
                run.setResponseTime(rd.get("responseTime") != null ? ((Number) rd.get("responseTime")).intValue() : 0);
                prompt.getRuns().add(run);
            }
        }
    }
}
