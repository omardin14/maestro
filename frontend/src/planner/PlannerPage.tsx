import { useCallback, useState } from 'react';
import { theme } from '../shared/theme';
import { planner } from '../api/client';
import { useWebSocket } from '../api/useWebSocket';
import { IntakeWizard } from './IntakeWizard';
import { ArtifactViewer } from './ArtifactViewer';

interface SessionState {
  messages?: Array<{ type: string; content: string }>;
  questionnaire?: Record<string, unknown>;
  project_analysis?: Record<string, unknown>;
  epics?: Array<Record<string, unknown>>;
  stories?: Array<Record<string, unknown>>;
  tasks?: Array<Record<string, unknown>>;
  sprints?: Array<Record<string, unknown>>;
  pending_review?: string;
  [key: string]: unknown;
}

export function PlannerPage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [state, setState] = useState<SessionState>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onMessage = useCallback((event: { type: string; data: Record<string, unknown> }) => {
    if (event.type === 'state_update') {
      setState(event.data as SessionState);
    }
  }, []);

  const { connected } = useWebSocket({
    url: sessionId ? `/ws/planner/${sessionId}` : '/ws/planner/_',
    onMessage,
    reconnect: !!sessionId,
  });

  const createSession = async () => {
    setLoading(true);
    setError(null);
    try {
      const { session_id } = await planner.createSession({ intake_mode: 'smart' });
      setSessionId(session_id);
      // Send initial empty message to trigger first question
      const result = await planner.sendMessage(session_id, '');
      setState(result.state as SessionState);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (content: string) => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    try {
      const result = await planner.sendMessage(sessionId, content);
      setState(result.state as SessionState);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  const submitReview = async (decision: string, feedback = '') => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const result = await planner.submitReview(sessionId, decision, feedback);
      setState(result.state as SessionState);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  // Determine current stage
  const hasAnalysis = !!state.project_analysis;
  const hasEpics = (state.epics?.length ?? 0) > 0;
  const hasStories = (state.stories?.length ?? 0) > 0;
  const hasTasks = (state.tasks?.length ?? 0) > 0;
  const hasSprints = (state.sprints?.length ?? 0) > 0;

  if (!sessionId) {
    return (
      <div style={{ padding: 48, textAlign: 'center', fontFamily: theme.fonts.mono }}>
        <h2 style={{ color: theme.colors.accent, marginBottom: 16 }}>New Planning Session</h2>
        <p style={{ color: theme.colors.textMuted, marginBottom: 24 }}>
          Start a new project planning session. The AI will guide you through intake questions,
          then generate epics, stories, tasks, and sprint plans.
        </p>
        <button
          onClick={createSession}
          disabled={loading}
          style={{
            padding: '12px 32px',
            background: theme.colors.accent,
            color: theme.colors.bg,
            border: 'none',
            borderRadius: theme.radii.md,
            fontSize: '1rem',
            fontWeight: 600,
            cursor: 'pointer',
            fontFamily: theme.fonts.mono,
          }}
        >
          {loading ? 'Creating...' : 'Start Session'}
        </button>
        {error && <p style={{ color: theme.colors.error, marginTop: 16 }}>{error}</p>}
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 56px)' }}>
      {/* Status bar */}
      <div
        style={{
          padding: '8px 24px',
          background: theme.colors.surface,
          borderBottom: `1px solid ${theme.colors.border}`,
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '0.8rem',
          color: theme.colors.textMuted,
          fontFamily: theme.fonts.mono,
        }}
      >
        <span>Session: {sessionId}</span>
        <span style={{ color: connected ? theme.colors.success : theme.colors.error }}>
          {connected ? 'Connected' : 'Disconnected'}
        </span>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, overflow: 'auto', padding: 24 }}>
        {!hasAnalysis && <IntakeWizard state={state} onSend={sendMessage} loading={loading} />}
        {hasAnalysis && <ArtifactViewer state={state} onReview={submitReview} loading={loading} />}
      </div>

      {error && (
        <div style={{ padding: '8px 24px', background: `${theme.colors.error}20`, color: theme.colors.error, fontSize: '0.85rem' }}>
          {error}
        </div>
      )}
    </div>
  );
}
