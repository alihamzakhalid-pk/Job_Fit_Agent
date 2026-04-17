export default function Pipeline({ steps, stepIndex, completedSteps }) {
  return (
    <div style={s.wrap}>
      <div style={s.header} className="fade-up">
        <div style={s.spinner} />
        <div>
          <h2 style={s.title}>Agents Running</h2>
          <p style={s.sub}>Multi-agent pipeline processing your resume in real-time</p>
        </div>
      </div>

      <div style={s.steps}>
        {steps.map((step, i) => {
          const done    = completedSteps.includes(step.id)
          const active  = i === stepIndex && !done
          const waiting = i > stepIndex

          return (
            <div
              key={step.id}
              style={{
                ...s.step,
                ...(done   ? s.stepDone   : {}),
                ...(active ? s.stepActive : {}),
                ...(waiting? s.stepWait   : {}),
              }}
              className="fade-up"
            >
              {/* connector line */}
              {i < steps.length - 1 && (
                <div style={{ ...s.connector, ...(done ? s.connectorDone : {}) }} />
              )}

              {/* icon */}
              <div style={{
                ...s.icon,
                ...(done   ? s.iconDone   : {}),
                ...(active ? s.iconActive : {}),
              }}>
                {done ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                ) : active ? (
                  <div style={s.pulse} />
                ) : (
                  <span style={s.stepNum}>{i + 1}</span>
                )}
              </div>

              {/* content */}
              <div style={s.stepContent}>
                <div style={s.stepLabel}>{step.label}</div>
                <div style={s.stepDesc}>
                  {done ? '✓ Complete' : active ? step.desc : 'Waiting...'}
                </div>
              </div>

              {/* status badge */}
              <div style={{
                ...s.badge,
                ...(done   ? s.badgeDone   : {}),
                ...(active ? s.badgeActive : {}),
              }}>
                {done ? 'Done' : active ? 'Running' : 'Pending'}
              </div>
            </div>
          )
        })}
      </div>

      <div style={s.footer}>
        <div style={s.footerBar}>
          <div style={{
            ...s.footerFill,
            width: `${Math.round((completedSteps.length / steps.length) * 100)}%`
          }} />
        </div>
        <span style={s.footerText}>
          {completedSteps.length}/{steps.length} agents complete
        </span>
      </div>
    </div>
  )
}

const s = {
  wrap: { maxWidth: '680px', margin: '0 auto' },
  header: {
    display: 'flex', alignItems: 'center', gap: '20px',
    marginBottom: '44px',
  },
  spinner: {
    width: '44px', height: '44px', borderRadius: '50%', flexShrink: 0,
    border: '3px solid var(--bg3)',
    borderTopColor: 'var(--accent)',
    animation: 'spin 0.8s linear infinite',
  },
  title: {
    fontFamily: 'var(--font-head)', fontSize: '26px',
    fontWeight: 700, color: 'var(--text)', marginBottom: '4px',
  },
  sub: { fontSize: '14px', color: 'var(--muted)' },
  steps: { display: 'flex', flexDirection: 'column', gap: '0' },
  step: {
    display: 'flex', alignItems: 'center', gap: '16px',
    padding: '18px 20px', borderRadius: 'var(--radius)',
    border: '1.5px solid var(--border-section)',
    background: 'var(--bg2)', marginBottom: '8px',
    position: 'relative', transition: 'all 0.3s',
    opacity: 0.4,
    boxShadow: '0 0 1px rgba(255,255,255,0.08) inset',
  },
  stepDone: { opacity: 1, borderColor: 'rgba(52,211,153,0.2)', background: 'rgba(52,211,153,0.04)' },
  stepActive: { opacity: 1, borderColor: 'rgba(124,108,250,0.4)', background: 'rgba(124,108,250,0.05)', animation: 'glow 2s ease infinite' },
  stepWait: { opacity: 0.3 },
  connector: {
    position: 'absolute', left: '34px', bottom: '-9px',
    width: '2px', height: '9px', background: 'var(--border)', zIndex: 1,
  },
  connectorDone: { background: 'var(--green)' },
  icon: {
    width: '36px', height: '36px', borderRadius: '50%', flexShrink: 0,
    background: 'var(--bg3)', border: '1px solid var(--border)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    transition: 'all 0.3s',
  },
  iconDone: { background: 'rgba(52,211,153,0.15)', border: '1px solid var(--green)', color: 'var(--green)' },
  iconActive: { background: 'rgba(124,108,250,0.15)', border: '1px solid var(--accent)', color: 'var(--accent)' },
  pulse: {
    width: '10px', height: '10px', borderRadius: '50%',
    background: 'var(--accent)', animation: 'pulse 1s ease infinite',
  },
  stepNum: { fontSize: '13px', color: 'var(--muted)', fontWeight: 600 },
  stepContent: { flex: 1 },
  stepLabel: { fontSize: '14px', fontWeight: 600, color: 'var(--text)', marginBottom: '2px' },
  stepDesc: { fontSize: '12px', color: 'var(--muted)' },
  badge: {
    fontSize: '11px', padding: '4px 12px', borderRadius: '20px',
    background: 'var(--bg3)', color: '#ffffff',
    border: '1px solid var(--border)',
  },
  badgeDone: { background: 'rgba(52,211,153,0.1)', color: '#ffffff', border: '1px solid rgba(52,211,153,0.2)' },
  badgeActive: { background: 'rgba(124,108,250,0.1)', color: '#ffffff', border: '1px solid rgba(124,108,250,0.3)' },
  footer: { marginTop: '32px', display: 'flex', alignItems: 'center', gap: '14px' },
  footerBar: {
    flex: 1, height: '4px', background: 'var(--bg3)',
    borderRadius: '2px', overflow: 'hidden',
  },
  footerFill: {
    height: '100%', borderRadius: '2px',
    background: 'linear-gradient(90deg, var(--accent), var(--green))',
    transition: 'width 0.5s ease',
  },
  footerText: { fontSize: '12px', color: 'var(--muted)', whiteSpace: 'nowrap' },
}
