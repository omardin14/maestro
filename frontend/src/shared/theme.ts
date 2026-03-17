/** Maestro design system — dark theme with amber accents. */

export const theme = {
  colors: {
    bg: '#080808',
    surface: '#1a1a1a',
    surfaceHover: '#242424',
    border: '#2a2a2a',
    text: '#e0e0e0',
    textMuted: '#888888',
    accent: '#f59e0b',       // amber-500
    accentDark: '#d97706',   // amber-600
    success: '#22c55e',      // green-500
    error: '#ef4444',        // red-500
    warning: '#f59e0b',      // amber-500
    info: '#3b82f6',         // blue-500
    critical: '#ef4444',
    high: '#f97316',
    medium: '#3b82f6',
    low: '#94a3b8',
  },
  fonts: {
    mono: "'IBM Plex Mono', 'Fira Code', monospace",
    sans: "'IBM Plex Sans', -apple-system, sans-serif",
  },
  radii: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    full: '999px',
  },
} as const;

export type Theme = typeof theme;
