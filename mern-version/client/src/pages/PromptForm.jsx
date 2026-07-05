import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/api';

const EMPTY_FORM = {
  title: '',
  content: '',
  notes: '',
  version: '',
  rating: 0,
  tags: [],
};

function PromptForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(id);

  const [form, setForm] = useState(() => ({ ...EMPTY_FORM }));
  const [allTags, setAllTags] = useState(() => []);
  const [showNewTag, setShowNewTag] = useState(false);
  const [newTag, setNewTag] = useState(() => ({ title: '', notes: '' }));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [fetching, setFetching] = useState(isEdit);

  // Load all tags + (edit mode) current prompt
  useEffect(() => {
    api.get('/tags').then((r) => setAllTags(r.data)).catch(() => {});

    if (!isEdit) return;

    (async () => {
      try {
        const r = await api.get(`/prompts/${id}`);
        const p = r.data;
        setForm({
          title: p.title,
          content: p.content,
          notes: p.notes,
          version: p.version || '',
          rating: p.rating || 0,
          tags: p.tags ? p.tags.map((t) => t._id) : [],
        });
      } catch (err) {
        setError(err.message);
      } finally {
        setFetching(false);
      }
    })();
  }, [id, isEdit]);

  const handleChange = useCallback(
    (field) => (e) => setForm((prev) => ({ ...prev, [field]: e.target.value })),
    []
  );

  const handleTagToggle = useCallback((tagId) => {
    setForm((prev) => {
      const has = prev.tags.includes(tagId);
      return {
        ...prev,
        tags: has
          ? prev.tags.filter((tid) => tid !== tagId)
          : [...prev.tags, tagId],
      };
    });
  }, []);

  const handleCreateTag = async (e) => {
    e.preventDefault();
    if (!newTag.title.trim() || !newTag.notes.trim()) return;
    try {
      const r = await api.post('/tags', newTag);
      setAllTags((prev) => [...prev, r.data]);
      setForm((prev) => ({ ...prev, tags: [...prev.tags, r.data._id] }));
      setNewTag({ title: '', notes: '' });
      setShowNewTag(false);
    } catch (err) {
      alert('创建标签失败: ' + err.message);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const body = {
        title: form.title,
        content: form.content,
        notes: form.notes,
        version: form.version || undefined,
        rating: form.rating || undefined,
        tags: form.tags,
      };
      if (isEdit) {
        await api.put(`/prompts/${id}`, body);
      } else {
        await api.post('/prompts', body);
      }
      navigate('/prompts');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // --- Fetching existing prompt ---
  if (fetching) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg">
        <p className="text-text-dim">加载中...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg">
      <div className="mx-auto max-w-2xl px-6 py-8 animate-slide-up">
        <h2 className="mb-8 text-2xl font-bold text-text text-balance">
          {isEdit ? '编辑提示词' : '新建提示词'}
        </h2>

        {error ? (
          <div
            className="mb-6 rounded-lg border border-danger-dim bg-danger/5 p-3 text-sm text-danger"
            role="alert"
          >
            {error}
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="space-y-5" noValidate>
          {/* ── Title ── */}
          <div>
            <label
              htmlFor="prompt-title"
              className="mb-1.5 block text-sm font-medium text-text-muted"
            >
              名称 <span className="text-danger">*</span>
            </label>
            <input
              id="prompt-title"
              type="text"
              value={form.title}
              onChange={handleChange('title')}
              maxLength={100}
              required
              autoComplete="off"
              placeholder="如：通用代码生成器"
              className="w-full rounded-lg border border-border bg-surface px-4 py-2.5 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none focus:ring-1 focus:ring-amber-400/20"
            />
          </div>

          {/* ── Content ── */}
          <div>
            <label
              htmlFor="prompt-content"
              className="mb-1.5 block text-sm font-medium text-text-muted"
            >
              提示词内容 <span className="text-danger">*</span>
            </label>
            <textarea
              id="prompt-content"
              value={form.content}
              onChange={handleChange('content')}
              required
              rows={8}
              placeholder="输入完整提示词文本..."
              className="w-full resize-y rounded-lg border border-border bg-surface px-4 py-2.5 font-mono text-sm leading-relaxed text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none focus:ring-1 focus:ring-amber-400/20 scrollbar-thin"
            />
          </div>

          {/* ── Notes ── */}
          <div>
            <label
              htmlFor="prompt-notes"
              className="mb-1.5 block text-sm font-medium text-text-muted"
            >
              反思 & 思路 <span className="text-danger">*</span>
            </label>
            <textarea
              id="prompt-notes"
              value={form.notes}
              onChange={handleChange('notes')}
              required
              rows={3}
              placeholder="这版为什么有效/失败？思路来源是什么？不同模型的表现差异？"
              className="w-full resize-y rounded-lg border border-border bg-surface px-4 py-2.5 text-sm leading-relaxed text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none focus:ring-1 focus:ring-amber-400/20 scrollbar-thin"
            />
          </div>

          {/* ── Version + Rating ── */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label
                htmlFor="prompt-version"
                className="mb-1.5 block text-sm font-medium text-text-muted"
              >
                版本号
              </label>
              <input
                id="prompt-version"
                type="text"
                value={form.version}
                onChange={handleChange('version')}
                placeholder="v1 / v2 / ..."
                autoComplete="off"
                className="w-full rounded-lg border border-border bg-surface px-4 py-2.5 font-mono text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none focus:ring-1 focus:ring-amber-400/20"
              />
            </div>
            <div>
              <fieldset>
                <legend className="mb-1.5 text-sm font-medium text-text-muted">
                  评分
                </legend>
                <div className="flex items-center gap-1 pt-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() =>
                        setForm((prev) => ({
                          ...prev,
                          rating: prev.rating === star ? 0 : star,
                        }))
                      }
                      className={`text-xl transition-all active:scale-90 focus-visible:outline-2 focus-visible:outline-amber-400 rounded ${
                        star <= form.rating
                          ? 'text-amber-400'
                          : 'text-zinc-700 hover:text-zinc-500'
                      }`}
                      aria-label={`${star} 星`}
                    >
                      ★
                    </button>
                  ))}
                  {form.rating > 0 ? (
                    <span className="ml-2 font-mono text-xs text-text-muted">
                      {form.rating}/5
                    </span>
                  ) : null}
                </div>
              </fieldset>
            </div>
          </div>

          {/* ── Tags ── */}
          <div>
            <div className="mb-1.5 flex items-center justify-between">
              <span className="text-sm font-medium text-text-muted">标签</span>
              <button
                type="button"
                onClick={() => setShowNewTag((prev) => !prev)}
                className="text-xs font-medium text-amber-400 hover:text-amber-300 transition-colors"
              >
                + 新建标签
              </button>
            </div>

            {/* Inline create tag */}
            {showNewTag ? (
              <div className="mb-3 rounded-lg border border-border bg-bg p-3">
                <div className="mb-2 flex gap-2">
                  <input
                    type="text"
                    placeholder="标签名"
                    value={newTag.title}
                    onChange={(e) =>
                      setNewTag((prev) => ({ ...prev, title: e.target.value }))
                    }
                    maxLength={100}
                    autoComplete="off"
                    className="flex-1 rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none"
                  />
                  <input
                    type="text"
                    placeholder="说明"
                    value={newTag.notes}
                    onChange={(e) =>
                      setNewTag((prev) => ({ ...prev, notes: e.target.value }))
                    }
                    autoComplete="off"
                    className="flex-1 rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleCreateTag}
                    className="rounded-md bg-amber-400 px-3 py-1 text-xs font-semibold text-bg hover:bg-amber-300 active:scale-[0.97] transition-all"
                  >
                    创建并添加
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowNewTag(false)}
                    className="rounded-md px-3 py-1 text-xs text-text-dim hover:text-text-muted transition-colors"
                  >
                    取消
                  </button>
                </div>
              </div>
            ) : null}

            {/* Multi-select tag list */}
            <div className="scrollbar-thin max-h-44 space-y-0.5 overflow-y-auto rounded-lg border border-border bg-surface p-2">
              {allTags.length === 0 ? (
                <p className="py-3 text-center text-xs text-text-dim">
                  暂无标签，点击"+ 新建标签"创建
                </p>
              ) : (
                allTags.map((tag) => {
                  const checked = form.tags.includes(tag._id);
                  return (
                    <label
                      key={tag._id}
                      className={`flex cursor-pointer items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors hover:bg-white/[0.04] ${
                        checked ? 'text-text' : 'text-text-muted'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => handleTagToggle(tag._id)}
                        className="accent-amber-400"
                      />
                      <span className="font-medium">{tag.title}</span>
                      <span className="truncate text-xs text-text-dim">
                        — {tag.notes}
                      </span>
                    </label>
                  );
                })
              )}
            </div>

            {/* Selected tags preview */}
            {form.tags.length > 0 ? (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {form.tags.map((tid) => {
                  const tag = allTags.find((t) => t._id === tid);
                  return tag ? (
                    <span
                      key={tid}
                      className="inline-flex items-center gap-1 rounded-full border border-amber-400/20 bg-amber-400/5 px-2.5 py-1 text-xs font-medium text-amber-400"
                    >
                      {tag.title}
                      <button
                        type="button"
                        onClick={() => handleTagToggle(tid)}
                        className="ml-0.5 rounded-full p-0.5 text-amber-400/60 hover:text-amber-400"
                        aria-label={`移除 ${tag.title}`}
                      >
                        ×
                      </button>
                    </span>
                  ) : null;
                })}
              </div>
            ) : null}
          </div>

          {/* ── Submit ── */}
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-amber-400 px-6 py-2.5 text-sm font-semibold text-bg hover:bg-amber-300 disabled:opacity-50 transition-all active:scale-[0.97]"
            >
              {loading ? '保存中...' : isEdit ? '保存修改' : '创建提示词'}
            </button>
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="rounded-lg border border-border px-6 py-2.5 text-sm font-medium text-text-muted hover:text-text hover:border-border-hover transition-colors"
            >
              取消
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default PromptForm;
