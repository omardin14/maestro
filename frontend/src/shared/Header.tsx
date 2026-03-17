import { Link, useLocation } from 'react-router-dom';
import { theme } from './theme';

export function Header() {
  const location = useLocation();
  const isPlanner = location.pathname.startsWith('/planner');
  const isDashboard = location.pathname.startsWith('/dashboard');

  return (
    <header
      style={{
        background: theme.colors.surface,
        borderBottom: `1px solid ${theme.colors.border}`,
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        height: 56,
        fontFamily: theme.fonts.mono,
      }}
    >
      <Link
        to="/"
        style={{
          color: theme.colors.accent,
          fontWeight: 700,
          fontSize: '1.1rem',
          textDecoration: 'none',
          letterSpacing: '0.05em',
          marginRight: 32,
        }}
      >
        MAESTRO
      </Link>
      <nav style={{ display: 'flex', gap: 4 }}>
        <NavTab to="/planner" active={isPlanner}>Planner</NavTab>
        <NavTab to="/dashboard" active={isDashboard}>Dashboard</NavTab>
      </nav>
    </header>
  );
}

function NavTab({ to, active, children }: { to: string; active: boolean; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      style={{
        padding: '8px 16px',
        borderRadius: theme.radii.sm,
        color: active ? theme.colors.accent : theme.colors.textMuted,
        background: active ? `${theme.colors.accent}15` : 'transparent',
        textDecoration: 'none',
        fontSize: '0.85rem',
        fontWeight: 500,
        fontFamily: theme.fonts.mono,
      }}
    >
      {children}
    </Link>
  );
}
