package com.mission5.notes.controller;

import com.mission5.notes.dto.ApiResponse;
import com.mission5.notes.entity.Tag;
import com.mission5.notes.repository.TagRepository;
import jakarta.validation.Valid;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/tags")
public class TagController {

    private final TagRepository repo;

    public TagController(TagRepository repo) { this.repo = repo; }

    @GetMapping
    public ApiResponse<Iterable<Tag>> list() {
        return ApiResponse.success(repo.findAll(Sort.by(Sort.Direction.DESC, "updatedAt")));
    }

    @GetMapping("/{id}")
    public ApiResponse<Tag> get(@PathVariable Long id) {
        return repo.findById(id)
            .map(ApiResponse::success)
            .orElseGet(() -> ApiResponse.error("标签不存在"));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ApiResponse<Tag> create(@Valid @RequestBody Tag tag) {
        return ApiResponse.success(repo.save(tag));
    }

    @PutMapping("/{id}")
    public ApiResponse<Tag> update(@PathVariable Long id, @RequestBody Map<String, Object> body) {
        return repo.findById(id).map(tag -> {
            if (body.containsKey("title")) tag.setTitle((String) body.get("title"));
            if (body.containsKey("notes")) tag.setNotes((String) body.get("notes"));
            return ApiResponse.success(repo.save(tag));
        }).orElseGet(() -> ApiResponse.error("标签不存在"));
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Map<String, String>> delete(@PathVariable Long id) {
        if (!repo.existsById(id)) return ApiResponse.error("标签不存在");
        repo.deleteById(id);
        return ApiResponse.success(Map.of("message", "删除成功"));
    }
}
