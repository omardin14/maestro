import { useState } from 'react';
import { theme } from '../shared/theme';

interface Props {
  state: Record<string, unknown>;
  onSend: (content: string) => Promise<void>;
  loading: boolean;
}

const PHASE_LABELS: Record<string, string> = {
  project_context: 'Project Context',
  team_and_capacity: 'Team & Capacity',
  technical_context: 'Technical Context',
  codebase_context: 'Codebase Context',
  risks_and_unknowns: 'Risks & Unknowns',
  preferences: 'Preferences',
  capacity_planning: 'Capacity Planning',
};

export function IntakeWizard({ state, onSend, loading }: Props) {
  const [input, setInput] = useState('');
  const questionnaire = state.questionnaire as Record<string, unknown> | undefined;
  const messages = (state.messages as Array<{ type: string; content: string }>) || [];

  const currentPhase = questionnaire?.current_phase as string | undefined;
  const progress = (questionnaire?.progress as number) || 0;

  // Get the last AI message as the current question
  const lastAIMessage = [...messages].reverse().find((m) => m.type === 'AIMessage');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() && !loading) return;
    await onSend(input.trim());
    setInput('');
  };

  return (
    <div style={{ maxWidth: 700, margin: '0 auto', fontFamily: theme.fonts.mono }}>
      {/* Progress bar */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
          <span style={{ color: theme.colors.textMuted, fontSize: '0.8rem' }}>
            {currentPhase ? PHASE_LABELS[currentPhase] || currentPhase : 'Starting...'}
          </span>
          <span style={{ color: theme.colors.textMuted, fontSize: '0.8rem' }}>
            {Math.round(progress * 100)}%
          </span>
        </div>
        <div
          style={{
            height: 4,
            background: theme.colors.border,
            borderRadius: theme.radii.full,
          }}
        >
          <div
            style={{
              height: '100%',
              width: `${progress * 100}%`,
              background: theme.colors.accent,
              borderRadius: theme.radii.full,
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      </div>

      {/* Phase indicators */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24, flexWrap: 'wrap' }}>
        {Object.entries(PHASE_LABELS).map(([key, label]) => {
          const isActive = key === currentPhase;
          return (
            <span
              key={key}
              style={{
                padding: '4px 10px',
                borderRadius: theme.radii.full,
                fontSize: '0.7rem',
                fontWeight: 500,
                color: isActive ? theme.colors.accent : theme.colors.textMuted,
                background: isActive ? `${theme.colors.accent}15` : 'transparent',
                border: `1px solid ${isActive ? theme.colors.accent + '33' : theme.colors.border}`,
              }}
            >
              {label}
            </span>
          );
        })}
      </div>

      {/* Current question */}
      {lastAIMessage && (
        <div
          style={{
            padding: 20,
            background: theme.colors.surface,
            borderRadius: theme.radii.md,
            border: `1px solid ${theme.colors.border}`,
            marginBottom: 20,
            whiteSpace: 'pre-wrap',
            color: theme.colors.text,
            fontSize: '0.9rem',
            lineHeight: 1.6,
          }}
        >
          {lastAIMessage.content}
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your answer..."
          disabled={loading}
          autoFocus
          style={{
            flex: 1,
            padding: '12px 16px',
            background: theme.colors.surface,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: theme.radii.md,
            color: theme.colors.text,
            fontSize: '0.9rem',
            fontFamily: theme.fonts.mono,
            outline: 'none',
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: '12px 24px',
            background: theme.colors.accent,
            color: theme.colors.bg,
            border: 'none',
            borderRadius: theme.radii.md,
            fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
            fontFamily: theme.fonts.mono,
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? '...' : 'Send'}
        </button>
      </form>
    </div>
  );
}
