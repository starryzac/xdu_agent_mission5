import { Link } from 'react-router-dom';

function TagBadge({ tag, onRemove }) {
  const baseClass =
    'inline-flex items-center gap-1 rounded-full border border-amber-400/20 bg-amber-400/5 px-2.5 py-1 text-xs font-medium text-amber-400 transition-colors hover:border-amber-400/40 hover:bg-amber-400/10';

  if (onRemove) {
    return (
      <span className={baseClass}>
        {tag.title}
        <button
          type="button"
          onClick={onRemove}
          className="ml-0.5 rounded-full p-0.5 text-amber-400/60 hover:text-amber-400 focus-visible:outline-2 focus-visible:outline-amber-400"
          aria-label={`移除标签 ${tag.title}`}
        >
          ×
        </button>
      </span>
    );
  }

  return (
    <Link
      to={`/tags/${tag._id}`}
      onClick={(e) => e.stopPropagation()}
      className={baseClass}
    >
      {tag.title}
    </Link>
  );
}

export default TagBadge;
