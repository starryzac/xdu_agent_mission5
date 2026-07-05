import { Link } from 'react-router-dom';
import TagBadge from './TagBadge';

function PromptCard({ prompt }) {
  return (
    <Link
      to={`/prompts/${prompt._id}`}
      className="card card-hover group block p-5 no-underline"
    >
      {/* Top row: title + rating + version */}
      <div className="mb-3 flex items-start justify-between gap-4">
        <h3 className="truncate text-base font-semibold text-text group-hover:text-amber-400 transition-colors">
          {prompt.title}
        </h3>
        <div className="flex shrink-0 items-center gap-3 text-sm">
          {prompt.rating > 0 ? (
            <span
              className="flex items-center gap-0.5 font-mono text-xs tracking-wider"
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
            <span className="rounded-md bg-white/[0.04] px-2 py-0.5 font-mono text-[11px] text-text-muted">
              {prompt.version}
            </span>
          ) : null}
        </div>
      </div>

      {/* Content preview */}
      <p className="mb-3 line-clamp-2 text-sm leading-relaxed text-text-muted">
        {prompt.content}
      </p>

      {/* Bottom row: tags + date */}
      <div className="flex flex-wrap items-center gap-2">
        {prompt.tags.length > 0
          ? prompt.tags.map((tag) => <TagBadge key={tag._id} tag={tag} />)
          : null}
        <span className="ml-auto text-xs text-text-dim">
          {new Date(prompt.updatedAt).toLocaleDateString('zh-CN')}
        </span>
      </div>
    </Link>
  );
}

export default PromptCard;
