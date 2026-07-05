import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/api';
import Layout from '../components/Layout';
import PromptCard from '../components/PromptCard';

function PromptList() {
  const [prompts, setPrompts] = useState(() => []);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchPrompts = useCallback(async () => {
    try {
      setError('');
      setLoading(true);
      const res = await api.get('/prompts');
      setPrompts(res.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchPrompts(); }, [fetchPrompts]);

  const handleDelete = useCallback(
    async (id) => {
      if (!window.confirm('确定删除这条提示词吗？')) return;
      try {
        await api.del(`/prompts/${id}`);
        setPrompts((prev) => prev.filter((p) => p._id !== id));
      } catch (err) {
        alert('删除失败: ' + err.message);
      }
    },
    []
  );

  // Derive empty state during render, not effect
  const isEmpty = !loading && prompts.length === 0;

  return (
    <Layout>
      <div className="mb-8 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-text text-balance">
          提示词列表
        </h2>
        <Link
          to="/prompts/new"
          className="inline-flex items-center gap-1.5 rounded-lg bg-amber-400 px-4 py-2 text-sm font-semibold text-bg transition-all hover:bg-amber-300 focus-visible:outline-2 focus-visible:outline-amber-400 focus-visible:outline-offset-2 active:scale-[0.97]"
        >
          + 新建提示词
        </Link>
      </div>

      {error ? (
        <div
          className="mb-6 rounded-lg border border-danger-dim bg-danger/5 p-4 text-sm text-danger"
          role="alert"
        >
          <p>{error}</p>
          <button
            onClick={fetchPrompts}
            className="mt-2 text-danger underline hover:no-underline"
          >
            重试
          </button>
        </div>
      ) : null}

      {loading ? (
        <p className="py-16 text-center text-text-dim animate-fade-in">
          加载中...
        </p>
      ) : isEmpty ? (
        <div className="py-20 text-center animate-slide-up">
          <p className="text-5xl">🧪</p>
          <p className="mt-4 text-lg font-medium text-text-muted">
            实验室还是空的
          </p>
          <p className="mt-1 text-sm text-text-dim">
            创建第一条提示词，开始你的 AI 实验之旅
          </p>
          <Link
            to="/prompts/new"
            className="mt-6 inline-flex items-center gap-1.5 rounded-lg bg-amber-400 px-5 py-2.5 text-sm font-semibold text-bg hover:bg-amber-300 transition-colors"
          >
            + 创建第一条提示词
          </Link>
        </div>
      ) : (
        <div className="grid gap-4 grid-cols-[repeat(auto-fill,minmax(min(100%,420px),1fr))]">
          {prompts.map((p) => (
            <div key={p._id} className="group relative">
              <PromptCard prompt={p} />
              <button
                onClick={() => handleDelete(p._id)}
                className="absolute right-3 top-3 rounded-md bg-danger/10 px-2 py-1 text-xs text-danger opacity-0 transition-all hover:bg-danger/20 focus-visible:opacity-100 group-hover:opacity-100"
                aria-label={`删除 ${p.title}`}
              >
                删除
              </button>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}

export default PromptList;
