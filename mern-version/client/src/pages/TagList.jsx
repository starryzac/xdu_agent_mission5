import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/api';
import Layout from '../components/Layout';

function TagList() {
  const [tags, setTags] = useState(() => []);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [newTag, setNewTag] = useState(() => ({ title: '', notes: '' }));
  const [creating, setCreating] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState(() => ({ title: '', notes: '' }));

  const fetchTags = useCallback(async () => {
    try {
      setError('');
      setLoading(true);
      const res = await api.get('/tags');
      setTags(res.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchTags(); }, [fetchTags]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newTag.title.trim() || !newTag.notes.trim()) return;
    try {
      setCreating(true);
      const res = await api.post('/tags', newTag);
      setTags((prev) => [res.data, ...prev]);
      setNewTag({ title: '', notes: '' });
    } catch (err) {
      alert('创建失败: ' + err.message);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('删除标签不会删除关联的提示词，确定删除？')) return;
    try {
      await api.del(`/tags/${id}`);
      setTags((prev) => prev.filter((t) => t._id !== id));
    } catch (err) {
      alert('删除失败: ' + err.message);
    }
  };

  const startEdit = (tag) => {
    setEditingId(tag._id);
    setEditForm({ title: tag.title, notes: tag.notes });
  };

  const handleEdit = async (id) => {
    if (!editForm.title.trim() || !editForm.notes.trim()) return;
    try {
      const res = await api.put(`/tags/${id}`, editForm);
      setTags((prev) =>
        prev.map((t) => (t._id === id ? res.data : t))
      );
      setEditingId(null);
    } catch (err) {
      alert('编辑失败: ' + err.message);
    }
  };

  const isEmpty = !loading && tags.length === 0;

  return (
    <Layout>
      <h2 className="mb-8 text-2xl font-bold text-text text-balance">
        标签管理
      </h2>

      {error ? (
        <div
          className="mb-6 rounded-lg border border-danger-dim bg-danger/5 p-4 text-sm text-danger"
          role="alert"
        >
          <p>{error}</p>
          <button
            onClick={fetchTags}
            className="mt-2 underline hover:no-underline"
          >
            重试
          </button>
        </div>
      ) : null}

      {/* ── Inline create form ── */}
      <form
        onSubmit={handleCreate}
        className="mb-8 rounded-xl card p-5"
      >
        <h3 className="mb-3 text-sm font-medium text-text-muted">
          新建标签
        </h3>
        <div className="flex gap-3">
          <input
            type="text"
            placeholder="标签名称，如「代码生成」"
            value={newTag.title}
            onChange={(e) =>
              setNewTag((prev) => ({ ...prev, title: e.target.value }))
            }
            maxLength={100}
            required
            autoComplete="off"
            className="flex-1 rounded-lg border border-border bg-bg px-4 py-2.5 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none focus:ring-1 focus:ring-amber-400/20"
          />
          <input
            type="text"
            placeholder="说明：用途、适用场景"
            value={newTag.notes}
            onChange={(e) =>
              setNewTag((prev) => ({ ...prev, notes: e.target.value }))
            }
            required
            autoComplete="off"
            className="flex-[2] rounded-lg border border-border bg-bg px-4 py-2.5 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none focus:ring-1 focus:ring-amber-400/20"
          />
          <button
            type="submit"
            disabled={creating}
            className="rounded-lg bg-amber-400 px-6 py-2.5 text-sm font-semibold text-bg hover:bg-amber-300 disabled:opacity-50 transition-all active:scale-[0.97]"
          >
            {creating ? '创建中...' : '创建'}
          </button>
        </div>
      </form>

      {/* ── Tag list ── */}
      {loading ? (
        <p className="py-16 text-center text-text-dim">加载中...</p>
      ) : isEmpty ? (
        <div className="py-20 text-center animate-slide-up">
          <p className="text-5xl">🏷️</p>
          <p className="mt-4 text-lg font-medium text-text-muted">
            还没有标签
          </p>
          <p className="mt-1 text-sm text-text-dim">
            标签帮助你按组别分类管理提示词，使用上方表单创建第一个
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {tags.map((tag) => (
            <div
              key={tag._id}
              className="card card-hover flex items-center gap-4 p-4"
            >
              {editingId === tag._id ? (
                /* ── Editing mode ── */
                <>
                  <input
                    type="text"
                    value={editForm.title}
                    onChange={(e) =>
                      setEditForm((prev) => ({
                        ...prev,
                        title: e.target.value,
                      }))
                    }
                    maxLength={100}
                    autoComplete="off"
                    className="flex-1 rounded-md border border-border bg-bg px-3 py-2 text-sm text-text focus:border-amber-400/50 focus:outline-none"
                  />
                  <input
                    type="text"
                    value={editForm.notes}
                    onChange={(e) =>
                      setEditForm((prev) => ({
                        ...prev,
                        notes: e.target.value,
                      }))
                    }
                    autoComplete="off"
                    className="flex-[2] rounded-md border border-border bg-bg px-3 py-2 text-sm text-text focus:border-amber-400/50 focus:outline-none"
                  />
                  <button
                    onClick={() => handleEdit(tag._id)}
                    className="rounded-md bg-amber-400 px-4 py-2 text-xs font-semibold text-bg hover:bg-amber-300 active:scale-[0.97]"
                  >
                    保存
                  </button>
                  <button
                    onClick={() => setEditingId(null)}
                    className="rounded-md px-4 py-2 text-xs text-text-dim hover:text-text-muted transition-colors"
                  >
                    取消
                  </button>
                </>
              ) : (
                /* ── Display mode ── */
                <>
                  <Link
                    to={`/tags/${tag._id}`}
                    className="flex min-w-0 flex-1 items-center gap-3 no-underline hover:opacity-80 transition-opacity"
                  >
                    <span className="shrink-0 rounded-full border border-amber-400/20 bg-amber-400/5 px-3 py-1 text-sm font-medium text-amber-400">
                      {tag.title}
                    </span>
                    <span className="min-w-0 truncate text-sm text-text-muted">
                      {tag.notes}
                    </span>
                  </Link>
                  <span className="shrink-0 text-xs text-text-dim">
                    {new Date(tag.updatedAt).toLocaleDateString('zh-CN')}
                  </span>
                  <button
                    onClick={() => startEdit(tag)}
                    className="shrink-0 rounded-md px-2 py-1 text-xs font-medium text-text-dim hover:text-text hover:bg-white/[0.04] transition-colors"
                  >
                    编辑
                  </button>
                  <button
                    onClick={() => handleDelete(tag._id)}
                    className="shrink-0 rounded-md px-2 py-1 text-xs font-medium text-danger/70 hover:text-danger hover:bg-danger/5 transition-colors"
                  >
                    删除
                  </button>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}

export default TagList;
