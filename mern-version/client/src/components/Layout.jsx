import { Link, useLocation } from 'react-router-dom';

export default function Layout({ children }) {
  const { pathname } = useLocation();

  const linkClass = (path) => {
    const active = pathname.startsWith(path);
    return [
      'relative px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
      'focus-visible:outline-2 focus-visible:outline-amber-400 focus-visible:outline-offset-2',
      active
        ? 'text-amber-400 bg-amber-400/10'
        : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04]',
    ].join(' ');
  };

  return (
    <div className="min-h-screen bg-bg text-text">
      {/* Header — sticky with backdrop-blur */}
      <header className="sticky top-0 z-50 border-b border-border bg-bg/80 backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-page items-center justify-between px-6">
          <Link
            to="/prompts"
            className="flex items-center gap-2.5 text-text no-underline focus-visible:outline-2 focus-visible:outline-amber-400 focus-visible:outline-offset-2 rounded-lg"
          >
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-400/10 text-base">
              ⚡
            </span>
            <span className="text-lg font-semibold tracking-tight">
              Prompt Lab
            </span>
          </Link>
          <nav className="flex gap-1" aria-label="主导航">
            <Link to="/prompts" className={linkClass('/prompts')}>
              Prompts
            </Link>
            <Link to="/tags" className={linkClass('/tags')}>
              Tags
            </Link>
          </nav>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto max-w-page px-6 py-8 animate-fade-in">
        {children}
      </main>
    </div>
  );
}
