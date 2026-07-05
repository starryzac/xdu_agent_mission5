import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { api } from '../api/api';
import Layout from '../components/Layout';
import PromptCard from '../components/PromptCard';

function TagDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [tag, setTag] = useState(null);
  const [prompts, setPrompts] = useState(() => []);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState(false);
  const [editNotes, setEditNotes] = useState('');

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const [tagRes, promptsRes] = await Promise.all([
          api.get(`/tags/${id}`),
          api.get('/prompts'),
        ]);
        setTag(tagRes.data);
        setEditNotes(tagRes.data.notes);
        const filtered = promptsRes.data.filter((p) =>
          p.tags ? p.tags.some((t) => t._id === id) : false
        );
        setPrompts(filtered);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const handleSaveNotes = async () => {
    if (!editNotes.trim()) return;
    try {
      const res = await api.put(`/tags/${id}`, { notes: editNotes });
      setTag(res.data);
      setEditing(false);
    } catch (err) {
      alert('保存失败: ' + err.message);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('删除标签不会删除关联的提示词，确定删除？')) return;
    try {
      await api.del(`/tags/${id}`);
      navigate('/tags');
    } catch (err) {
      alert('删除失败: ' + err.message);
    }
  };

  // --- Loading ---
  if (loading) {
    return (
      <Layout>
        <p className="py-16 text-center text-text-dim">加载中...</p>
      </Layout>
    );
  }

  // --- Error ---
  if (error) {
    return (
      <Layout>
        <div
          className="rounded-lg border border-danger-dim bg-danger/5 p-8 text-center"
          role="alert"
        >
          <p className="text-danger">{error}</p>
          <Link
            to="/tags"
            className="mt-4 inline-block text-amber-400 hover:underline"
          >
            ← 返回标签列表
          </Link>
        </div>
      </Layout>
    );
  }

  if (!tag) return null;

  return (
    <Layout>
      {/* Breadcrumb */}
      <div className="mb-6">
        <Link
          to="/tags"
          className="text-sm text-text-dim hover:text-text-muted transition-colors"
        >
          ← 返回标签列表
        </Link>
      </div>

      {/* ── Tag header ── */}
      <div className="card mb-8 p-6">
        <div className="mb-4 flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="rounded-full border border-amber-400/20 bg-amber-400/5 px-4 py-1.5 text-lg font-semibold text-amber-400">
              {tag.title}
            </span>
            <span className="text-xs text-text-dim">
              创建于 {new Date(tag.createdAt).toLocaleString('zh-CN')}
            </span>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <button
              onClick={() => {
                setEditing((prev) => !prev);
                setEditNotes(tag.notes);
              }}
              className="rounded-lg px-3 py-1.5 text-sm font-medium text-text-dim hover:text-text hover:bg-white/[0.04] transition-colors"
            >
              {editing ? '取消编辑' : '编辑 notes'}
            </button>
            <button
              onClick={handleDelete}
              className="rounded-lg px-3 py-1.5 text-sm font-medium text-danger/70 hover:text-danger hover:bg-danger/5 transition-colors"
            >
              删除标签
            </button>
          </div>
        </div>

        {/* Notes */}
        {editing ? (
          <div className="flex gap-2">
            <textarea
              value={editNotes}
              onChange={(e) => setEditNotes(e.target.value)}
              rows={3}
              className="flex-1 resize-y rounded-lg border border-border bg-bg px-4 py-2.5 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none focus:ring-1 focus:ring-amber-400/20 scrollbar-thin"
            />
            <button
              onClick={handleSaveNotes}
              className="self-end rounded-lg bg-amber-400 px-4 py-2.5 text-sm font-semibold text-bg hover:bg-amber-300 active:scale-[0.97] transition-all"
            >
              保存
            </button>
          </div>
        ) : (
          <p className="rounded-lg bg-bg px-4 py-3 text-sm leading-relaxed text-text-muted">
            {tag.notes}
          </p>
        )}
      </div>

      {/* ── Prompts under this tag ── */}
      <h3 className="mb-4 text-lg font-semibold text-text">
        该标签下的提示词
        {prompts.length > 0 ? (
          <span className="ml-2 font-mono text-sm text-teal">
            {prompts.length}
          </span>
        ) : null}
      </h3>

      {prompts.length === 0 ? (
        <div className="py-16 text-center animate-slide-up">
          <p className="text-text-muted">该标签下还没有提示词</p>
          <Link
            to="/prompts/new"
            className="mt-3 inline-flex items-center gap-1.5 text-amber-400 hover:underline"
          >
            + 创建提示词并添加此标签
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 grid-cols-[repeat(auto-fill,minmax(min(100%,420px),1fr))]">
          {prompts.map((p) => (
            <PromptCard key={p._id} prompt={p} />
          ))}
        </div>
      )}
    </Layout>
  );
}

export default TagDetail;
