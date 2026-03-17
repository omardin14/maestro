import { useCallback, useState } from 'react';
import { theme } from '../shared/theme';
import { StatusBadge } from '../shared/StatusBadge';
import { useWebSocket } from '../api/useWebSocket';
import { runner } from '../api/client';

interface RunnerState {
  running: boolean;
  agents?: Array<{
    identifier: string;
    title: string;
    state_name: string;
    status: string;
    session_id?: string;
    runtime_s?: number;
    turn_count?: number;
    input_tokens?: number;
    output_tokens?: number;
    last_message?: string;
  }>;
  retrying?: Array<{
    identifier: string;
    attempt: number;
    due_at_ms: number;
    error: string;
  }>;
  totals?: {
    input_tokens: number;
    output_tokens: number;
    runtime_s: number;
  };
}

export function DashboardPage() {
  const [state, setState] = useState<RunnerState>({ running: false });

  const onMessage = useCallback((event: { type: string; data: Record<string, unknown> }) => {
    if (event.type === 'state_changed') {
      setState(event.data as unknown as RunnerState);
    }
  }, []);

  const { connected } = useWebSocket({
    url: '/ws/runner',
    onMessage,
  });

  const agents = state.agents || [];
  const retrying = state.retrying || [];
  const totals = state.totals || { input_tokens: 0, output_tokens: 0, runtime_s: 0 };

  return (
    <div style={{ padding: 24, fontFamily: theme.fonts.mono, maxWidth: 1200, margin: '0 auto' }}>
      {/* Metrics cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 32 }}>
        <MetricCard label="Running" value={agents.filter((a) => a.status === 'running').length} />
        <MetricCard label="Retrying" value={retrying.length} />
        <MetricCard label="Tokens" value={formatNumber(totals.input_tokens + totals.output_tokens)} />
        <MetricCard label="Runtime" value={formatDuration(totals.runtime_s)} />
      </div>

      {/* Connection status */}
      <div
        style={{
          marginBottom: 24,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <h2 style={{ fontSize: '1rem', color: theme.colors.text }}>Active Sessions</h2>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <span style={{ fontSize: '0.75rem', color: connected ? theme.colors.success : theme.colors.error }}>
            {connected ? 'Live' : 'Disconnected'}
          </span>
          <button
            onClick={() => runner.refresh()}
            style={{
              padding: '6px 16px',
              background: theme.colors.surface,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: theme.radii.sm,
              color: theme.colors.text,
              cursor: 'pointer',
              fontSize: '0.8rem',
              fontFamily: theme.fonts.mono,
            }}
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Session table */}
      {agents.length === 0 ? (
        <div
          style={{
            padding: 48,
            textAlign: 'center',
            color: theme.colors.textMuted,
            background: theme.colors.surface,
            borderRadius: theme.radii.md,
            border: `1px solid ${theme.colors.border}`,
          }}
        >
          {state.running ? 'No active agents. Waiting for issues...' : 'Orchestrator not running. Start with: maestro start'}
        </div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['Issue', 'State', 'Status', 'Session', 'Runtime', 'Turns', 'Tokens', 'Last Message'].map((h) => (
                <th
                  key={h}
                  style={{
                    textAlign: 'left',
                    padding: '10px 12px',
                    borderBottom: `1px solid ${theme.colors.border}`,
                    color: theme.colors.textMuted,
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {agents.map((agent) => (
              <tr key={agent.identifier} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                <td style={{ padding: '10px 12px', fontWeight: 500 }}>
                  {agent.identifier}
                  <div style={{ fontSize: '0.75rem', color: theme.colors.textMuted }}>{agent.title}</div>
                </td>
                <td style={{ padding: '10px 12px' }}>{agent.state_name}</td>
                <td style={{ padding: '10px 12px' }}>
                  <StatusBadge status={agent.status} />
                </td>
                <td style={{ padding: '10px 12px', fontSize: '0.75rem', color: theme.colors.textMuted }}>
                  {agent.session_id?.slice(0, 8) || '-'}
                </td>
                <td style={{ padding: '10px 12px', fontSize: '0.8rem' }}>
                  {agent.runtime_s ? formatDuration(agent.runtime_s) : '-'}
                </td>
                <td style={{ padding: '10px 12px', fontSize: '0.8rem' }}>{agent.turn_count || 0}</td>
                <td style={{ padding: '10px 12px', fontSize: '0.8rem' }}>
                  {formatNumber((agent.input_tokens || 0) + (agent.output_tokens || 0))}
                </td>
                <td
                  style={{
                    padding: '10px 12px',
                    fontSize: '0.75rem',
                    color: theme.colors.textMuted,
                    maxWidth: 200,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {agent.last_message || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Retry queue */}
      {retrying.length > 0 && (
        <>
          <h2 style={{ fontSize: '1rem', color: theme.colors.text, marginTop: 32, marginBottom: 16 }}>
            Retry Queue ({retrying.length})
          </h2>
          {retrying.map((entry) => (
            <div
              key={entry.identifier}
              style={{
                padding: '12px 16px',
                background: theme.colors.surface,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.radii.md,
                marginBottom: 8,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <div>
                <span style={{ fontWeight: 500 }}>{entry.identifier}</span>
                <span style={{ color: theme.colors.textMuted, marginLeft: 12, fontSize: '0.8rem' }}>
                  Attempt #{entry.attempt}
                </span>
              </div>
              <span style={{ color: theme.colors.error, fontSize: '0.8rem', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {entry.error}
              </span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div
      style={{
        background: theme.colors.surface,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.radii.md,
        padding: '20px 24px',
      }}
    >
      <div style={{ fontSize: '0.72rem', color: theme.colors.textMuted, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
        {label}
      </div>
      <div style={{ fontSize: '1.5rem', fontWeight: 700, color: theme.colors.text }}>
        {value}
      </div>
    </div>
  );
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}
