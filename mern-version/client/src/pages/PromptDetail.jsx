import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../api/api';
import Layout from '../components/Layout';
import TagBadge from '../components/TagBadge';

function PromptDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showRunForm, setShowRunForm] = useState(false);
  const modelInputRef = useRef(null);

  // Run form state — use refs for transient form values where possible,
  // but we need controlled inputs for the form, so useState is correct here
  const [newRun, setNewRun] = useState(() => ({
    model: '',
    tokens: 0,
    responseTime: 0,
  }));

  const fetchPrompt = useCallback(async () => {
    try {
      setLoading(true);
      const res = await api.get(`/prompts/${id}`);
      setPrompt(res.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { fetchPrompt(); }, [fetchPrompt]);

  // Focus model input when run form opens
  useEffect(() => {
    if (showRunForm && modelInputRef.current) {
      modelInputRef.current.focus();
    }
  }, [showRunForm]);

  const handleDelete = async () => {
    if (!window.confirm('确定删除这条提示词吗？')) return;
    try {
      await api.del(`/prompts/${id}`);
      navigate('/prompts');
    } catch (err) {
      alert('删除失败: ' + err.message);
    }
  };

  const handleAddRun = async (e) => {
    e.preventDefault();
    if (!newRun.model.trim()) return;
    try {
      const updatedRuns = [...(prompt.runs || []), { ...newRun }];
      const res = await api.put(`/prompts/${id}`, { runs: updatedRuns });
      setPrompt(res.data);
      setShowRunForm(false);
      setNewRun({ model: '', tokens: 0, responseTime: 0 });
    } catch (err) {
      alert('添加运行记录失败: ' + err.message);
    }
  };

  const handleDeleteRun = async (index) => {
    const updatedRuns = prompt.runs.filter((_, i) => i !== index);
    const res = await api.put(`/prompts/${id}`, { runs: updatedRuns });
    setPrompt(res.data);
  };

  // Derive values during render
  const hasRuns = prompt && prompt.runs && prompt.runs.length > 0;

  // --- Loading state ---
  if (loading) {
    return (
      <Layout>
        <p className="py-16 text-center text-text-dim">加载中...</p>
      </Layout>
    );
  }

  // --- Error state ---
  if (error) {
    return (
      <Layout>
        <div
          className="rounded-lg border border-danger-dim bg-danger/5 p-8 text-center"
          role="alert"
        >
          <p className="text-danger">{error}</p>
          <Link
            to="/prompts"
            className="mt-4 inline-block text-amber-400 hover:underline"
          >
            ← 返回列表
          </Link>
        </div>
      </Layout>
    );
  }

  if (!prompt) return null;

  return (
    <Layout>
      {/* Breadcrumb */}
      <div className="mb-6">
        <Link
          to="/prompts"
          className="text-sm text-text-dim hover:text-text-muted transition-colors"
        >
          ← 返回列表
        </Link>
      </div>

      <div className="card p-6">
        {/* ── Header: title + rating + version ── */}
        <div className="mb-6 flex items-start justify-between gap-4">
          <h2 className="text-2xl font-bold text-text text-balance">
            {prompt.title}
          </h2>
          <div className="flex shrink-0 items-center gap-4">
            {prompt.rating > 0 ? (
              <span
                className="text-lg"
                aria-label={`评分 ${prompt.rating}/5`}
              >
                <span className="text-amber-400">
                  {'★'.repeat(prompt.rating)}
                </span>
                <span className="text-zinc-700">
                  {'★'.repeat(5 - prompt.rating)}
                </span>
              </span>
            ) : null}
            {prompt.version ? (
              <span className="rounded-md bg-white/[0.04] px-3 py-1 font-mono text-sm text-text-muted">
                {prompt.version}
              </span>
            ) : null}
          </div>
        </div>

        {/* ── Tags ── */}
        {prompt.tags && prompt.tags.length > 0 ? (
          <div className="mb-5 flex flex-wrap gap-2">
            {prompt.tags.map((tag) => (
              <TagBadge key={tag._id} tag={tag} />
            ))}
          </div>
        ) : null}

        {/* ── Content ── */}
        <section className="mb-5">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-dim">
            提示词内容
          </h3>
          <pre className="scrollbar-thin overflow-auto rounded-lg bg-bg px-4 py-3 font-mono text-sm leading-relaxed text-text whitespace-pre-wrap">
            {prompt.content}
          </pre>
        </section>

        {/* ── Notes ── */}
        <section className="mb-6">
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-dim">
            反思 & 思路
          </h3>
          <p className="rounded-lg bg-bg px-4 py-3 text-sm leading-relaxed text-text-muted">
            {prompt.notes}
          </p>
        </section>

        {/* ── Runs Table ── */}
        <section className="mb-6">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-text-dim">
              运行记录
              {hasRuns ? (
                <span className="ml-2 font-mono text-teal">
                  {prompt.runs.length}
                </span>
              ) : null}
            </h3>
            <button
              onClick={() => setShowRunForm((prev) => !prev)}
              className="text-xs font-medium text-amber-400 hover:text-amber-300 transition-colors"
            >
              {showRunForm ? '取消' : '+ 新增记录'}
            </button>
          </div>

          {/* Add run form */}
          {showRunForm ? (
            <form
              onSubmit={handleAddRun}
              className="mb-4 grid grid-cols-[2fr_1fr_1fr_auto] gap-3 rounded-lg bg-bg p-4"
            >
              <input
                ref={modelInputRef}
                type="text"
                placeholder="模型名称，如 deepseek-v4-pro"
                value={newRun.model}
                onChange={(e) =>
                  setNewRun((prev) => ({ ...prev, model: e.target.value }))
                }
                required
                autoComplete="off"
                className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none"
              />
              <input
                type="number"
                placeholder="Tokens"
                value={newRun.tokens || ''}
                onChange={(e) =>
                  setNewRun((prev) => ({ ...prev, tokens: +e.target.value }))
                }
                min="0"
                inputMode="numeric"
                className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none"
              />
              <input
                type="number"
                placeholder="耗时 (ms)"
                value={newRun.responseTime || ''}
                onChange={(e) =>
                  setNewRun((prev) => ({
                    ...prev,
                    responseTime: +e.target.value,
                  }))
                }
                min="0"
                inputMode="numeric"
                className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text placeholder:text-text-dim focus:border-amber-400/50 focus:outline-none"
              />
              <button
                type="submit"
                className="rounded-md bg-amber-400 px-4 py-2 text-sm font-semibold text-bg hover:bg-amber-300 transition-colors active:scale-[0.97]"
              >
                添加
              </button>
            </form>
          ) : null}

          {/* Runs table */}
          {hasRuns ? (
            <div className="scrollbar-thin overflow-hidden rounded-lg border border-border">
              <table className="w-full text-left text-sm">
                <thead className="bg-bg text-text-dim">
                  <tr>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider">
                      模型
                    </th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider">
                      Tokens
                    </th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider">
                      耗时
                    </th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider">
                      时间
                    </th>
                    <th className="px-4 py-2.5 text-xs font-semibold uppercase tracking-wider" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {prompt.runs.map((run, i) => (
                    <tr key={i} className="text-text-muted hover:bg-white/[0.02]">
                      <td className="px-4 py-2.5 font-mono text-xs text-teal">
                        {run.model}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-xs">
                        {run.tokens?.toLocaleString()}
                      </td>
                      <td className="px-4 py-2.5 font-mono text-xs">
                        {run.responseTime}ms
                      </td>
                      <td className="px-4 py-2.5 text-xs text-text-dim">
                        {new Date(run.createdAt).toLocaleString('zh-CN')}
                      </td>
                      <td className="px-4 py-2.5">
                        <button
                          onClick={() => handleDeleteRun(i)}
                          className="text-xs text-danger/70 hover:text-danger transition-colors"
                        >
                          删除
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="py-6 text-center text-sm text-text-dim">
              还没有运行记录 — 点击"+ 新增记录"添加第一次实验
            </p>
          )}
        </section>

        {/* ── Timestamps ── */}
        <div className="mb-6 flex gap-6 text-xs text-text-dim">
          <span>
            创建于 {new Date(prompt.createdAt).toLocaleString('zh-CN')}
          </span>
          <span>
            更新于 {new Date(prompt.updatedAt).toLocaleString('zh-CN')}
          </span>
        </div>

        {/* ── Actions ── */}
        <div className="flex gap-3 border-t border-border pt-6">
          <Link
            to={`/prompts/${prompt._id}/edit`}
            className="inline-flex items-center rounded-lg bg-amber-400 px-5 py-2.5 text-sm font-semibold text-bg hover:bg-amber-300 transition-colors active:scale-[0.97]"
          >
            编辑
          </Link>
          <button
            onClick={handleDelete}
            className="inline-flex items-center rounded-lg border border-danger-dim px-5 py-2.5 text-sm font-medium text-danger hover:bg-danger/10 transition-colors"
          >
            删除
          </button>
        </div>
      </div>
    </Layout>
  );
}

export default PromptDetail;
