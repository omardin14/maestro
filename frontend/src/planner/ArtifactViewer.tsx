import { theme } from '../shared/theme';


interface Props {
  state: Record<string, unknown>;
  onReview: (decision: string, feedback?: string) => Promise<void>;
  loading: boolean;
}

export function ArtifactViewer({ state, onReview, loading }: Props) {
  const analysis = state.project_analysis as Record<string, unknown> | undefined;
  const epics = (state.epics as Array<Record<string, unknown>>) || [];
  const stories = (state.stories as Array<Record<string, unknown>>) || [];
  const tasks = (state.tasks as Array<Record<string, unknown>>) || [];
  const sprints = (state.sprints as Array<Record<string, unknown>>) || [];
  const pendingReview = state.pending_review as string | undefined;

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', fontFamily: theme.fonts.mono }}>
      {/* Project Analysis */}
      {analysis && (
        <Section title="Project Analysis">
          <Card>
            <h3 style={{ color: theme.colors.accent, marginBottom: 8 }}>
              {analysis.project_name as string}
            </h3>
            <p style={{ color: theme.colors.textMuted, marginBottom: 12 }}>
              {analysis.project_description as string}
            </p>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <Tag label={analysis.project_type as string} />
              <Tag label={`${analysis.sprint_length_weeks}w sprints x ${analysis.target_sprints}`} />
            </div>
          </Card>
        </Section>
      )}

      {/* Epics */}
      {epics.length > 0 && (
        <Section title={`Epics (${epics.length})`}>
          {epics.map((epic, i) => (
            <Card key={i}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                  <span style={{ color: theme.colors.textMuted, fontSize: '0.75rem', marginRight: 8 }}>
                    {epic.id as string}
                  </span>
                  <span style={{ fontWeight: 600 }}>{epic.title as string}</span>
                </div>
                <PriorityBadge priority={epic.priority as string} />
              </div>
              <p style={{ color: theme.colors.textMuted, marginTop: 6, fontSize: '0.85rem' }}>
                {epic.description as string}
              </p>
            </Card>
          ))}
        </Section>
      )}

      {/* Stories */}
      {stories.length > 0 && (
        <Section title={`User Stories (${stories.length})`}>
          {stories.map((story, i) => (
            <Card key={i} style={{ borderLeft: `3px solid ${theme.colors.accent}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                <div>
                  <span style={{ color: theme.colors.textMuted, fontSize: '0.75rem', marginRight: 8 }}>
                    {story.id as string}
                  </span>
                  <span style={{ fontWeight: 600 }}>{story.title as string}</span>
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                  <Tag label={`${story.story_points} pts`} color={theme.colors.success} />
                  <PriorityBadge priority={story.priority as string} />
                </div>
              </div>
              <p style={{ color: theme.colors.textMuted, marginTop: 6, fontSize: '0.85rem' }}>
                As a {story.persona as string}, I want to {story.goal as string}, so that {story.benefit as string}.
              </p>
            </Card>
          ))}
        </Section>
      )}

      {/* Tasks */}
      {tasks.length > 0 && (
        <Section title={`Tasks (${tasks.length})`}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.84rem' }}>
            <thead>
              <tr>
                {['ID', 'Label', 'Title', 'Description'].map((h) => (
                  <th
                    key={h}
                    style={{
                      textAlign: 'left',
                      padding: '8px 12px',
                      borderBottom: `1px solid ${theme.colors.border}`,
                      color: theme.colors.textMuted,
                      fontWeight: 600,
                      fontSize: '0.75rem',
                      textTransform: 'uppercase',
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tasks.map((task, i) => (
                <tr key={i} style={{ borderBottom: `1px solid ${theme.colors.border}` }}>
                  <td style={{ padding: '8px 12px', color: theme.colors.textMuted, fontFamily: theme.fonts.mono }}>
                    {task.id as string}
                  </td>
                  <td style={{ padding: '8px 12px' }}>
                    <Tag label={task.label as string} />
                  </td>
                  <td style={{ padding: '8px 12px', fontWeight: 500 }}>{task.title as string}</td>
                  <td style={{ padding: '8px 12px', color: theme.colors.textMuted }}>{task.description as string}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      )}

      {/* Sprints */}
      {sprints.length > 0 && (
        <Section title={`Sprint Plan (${sprints.length} sprints)`}>
          {sprints.map((sprint, i) => (
            <Card key={i} style={{ borderTop: `3px solid ${theme.colors.accent}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 600 }}>{sprint.name as string}</span>
                <Tag label={`${sprint.capacity_points} pts`} />
              </div>
              <p style={{ color: theme.colors.textMuted, marginTop: 6, fontSize: '0.85rem' }}>
                {sprint.goal as string}
              </p>
              <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
                {((sprint.story_ids as string[]) || []).map((sid) => (
                  <Tag key={sid} label={sid} />
                ))}
              </div>
            </Card>
          ))}
        </Section>
      )}

      {/* Review gate */}
      {pendingReview && (
        <div
          style={{
            position: 'sticky',
            bottom: 0,
            padding: 16,
            background: theme.colors.surface,
            borderTop: `1px solid ${theme.colors.border}`,
            display: 'flex',
            gap: 12,
            justifyContent: 'center',
          }}
        >
          <ReviewButton label="Accept" color={theme.colors.success} onClick={() => onReview('accept')} disabled={loading} />
          <ReviewButton label="Edit" color={theme.colors.accent} onClick={() => onReview('edit')} disabled={loading} />
          <ReviewButton label="Reject" color={theme.colors.error} onClick={() => onReview('reject')} disabled={loading} />
        </div>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section style={{ marginBottom: 32 }}>
      <h2
        style={{
          fontSize: '1rem',
          fontWeight: 700,
          color: theme.colors.text,
          borderBottom: `2px solid ${theme.colors.accent}`,
          paddingBottom: 8,
          marginBottom: 16,
          fontFamily: theme.fonts.mono,
        }}
      >
        {title}
      </h2>
      {children}
    </section>
  );
}

function Card({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div
      style={{
        background: theme.colors.surface,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.radii.md,
        padding: '16px 20px',
        marginBottom: 12,
        ...style,
      }}
    >
      {children}
    </div>
  );
}

function Tag({ label, color }: { label: string; color?: string }) {
  const c = color || theme.colors.textMuted;
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '2px 8px',
        borderRadius: theme.radii.full,
        fontSize: '0.72rem',
        fontWeight: 600,
        color: c,
        border: `1px solid ${c}33`,
        background: `${c}10`,
        fontFamily: theme.fonts.mono,
      }}
    >
      {label}
    </span>
  );
}

const priorityColors: Record<string, string> = {
  critical: theme.colors.critical,
  high: theme.colors.high,
  medium: theme.colors.medium,
  low: theme.colors.low,
};

function PriorityBadge({ priority }: { priority: string }) {
  const color = priorityColors[priority?.toLowerCase()] || theme.colors.textMuted;
  return <Tag label={priority?.toUpperCase() || ''} color={color} />;
}

function ReviewButton({
  label,
  color,
  onClick,
  disabled,
}: {
  label: string;
  color: string;
  onClick: () => void;
  disabled: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: '10px 28px',
        border: `1px solid ${color}`,
        borderRadius: theme.radii.md,
        background: `${color}15`,
        color,
        fontWeight: 600,
        cursor: disabled ? 'not-allowed' : 'pointer',
        fontFamily: theme.fonts.mono,
        fontSize: '0.85rem',
      }}
    >
      {label}
    </button>
  );
}
