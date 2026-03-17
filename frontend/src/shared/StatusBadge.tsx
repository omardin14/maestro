import { theme } from './theme';

const statusColors: Record<string, string> = {
  running: theme.colors.accent,
  succeeded: theme.colors.success,
  failed: theme.colors.error,
  retrying: theme.colors.warning,
  gate: theme.colors.info,
  pending: theme.colors.textMuted,
  streaming: theme.colors.accent,
};

interface Props {
  status: string;
}

export function StatusBadge({ status }: Props) {
  const color = statusColors[status.toLowerCase()] || theme.colors.textMuted;
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '2px 10px',
        borderRadius: theme.radii.full,
        fontSize: '0.75rem',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.05em',
        color,
        border: `1px solid ${color}33`,
        background: `${color}15`,
        fontFamily: theme.fonts.mono,
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: '50%',
          background: color,
        }}
      />
      {status}
    </span>
  );
}
