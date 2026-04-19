import { useState } from 'react'

const TABS = ['Skill Gaps', 'Resume Rewrite', 'Roadmap', 'Interview Prep', 'Sources']

export default function Dashboard({ report }) {
  const [tab, setTab] = useState(0)

  const match   = report.match_score || 0
  const atsB    = report.ats_score_before || 0
  const atsA    = report.ats_score_after || 0
  const imp     = report.ats_improvement || 0
  const conf    = Math.round((report.confidence_score || 0) * 100)
  const allGaps = [...(report.critical_gaps || []), ...(report.important_gaps || [])]

  return (
    <div className="fade-up">
      {/* Candidate header */}
      <div style={s.candHeader}>
        <div style={s.avatar}>{(report.candidate_name || 'C')[0].toUpperCase()}</div>
        <div>
          <h2 style={s.candName}>{report.candidate_name || 'Candidate'}</h2>
          <p style={s.candSub}>Analysis complete · Confidence {conf}%</p>
        </div>
        <div style={s.confBadge}>
          <span style={{ color: conf >= 70 ? 'var(--green)' : 'var(--amber)' }}>●</span>
          &nbsp;Agent confidence {conf}%
        </div>
      </div>

      {/* Metric cards */}
      <div style={s.metrics}>
        <MetricCard
          label="Job Match"
          value={`${match}%`}
          color={match >= 60 ? 'var(--green)' : match >= 40 ? 'var(--amber)' : 'var(--red)'}
          sub={match >= 60 ? 'Strong match' : match >= 40 ? 'Partial match' : 'Needs work'}
        />
        <MetricCard
          label="ATS Before"
          value={atsB}
          color="var(--red)"
          sub="Original score"
        />
        <MetricCard
          label="ATS After"
          value={atsA}
          color="var(--green)"
          sub="After rewrite"
        />
        <MetricCard
          label="Improvement"
          value={`+${imp}`}
          color="var(--accent2)"
          sub="ATS points gained"
        />
        <MetricCard
          label="Critical Gaps"
          value={report.critical_gaps?.length || 0}
          color="var(--amber)"
          sub="Must fix gaps"
        />
      </div>

      {/* ATS bar */}
      <div style={s.atsSection}>
        <div style={s.atsSectionTitle}>ATS Score Transformation</div>
        <div style={s.atsBars}>
          <AtsBar label="Before rewrite" score={atsB} color="var(--red)" />
          <AtsBar label="After rewrite" score={atsA} color="var(--green)" />
        </div>
      </div>

      {/* Tabs */}
      <div style={s.tabsRow}>
        {TABS.map((t, i) => (
          <button
            key={i}
            style={{ ...s.tabBtn, ...(tab === i ? s.tabActive : {}) }}
            onClick={() => setTab(i)}
          >
            {t}
            {i === 0 && allGaps.length > 0 && (
              <span style={s.tabBadge}>{allGaps.length}</span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div style={s.tabContent}>
        {tab === 0 && <GapsTab report={report} allGaps={allGaps} />}
        {tab === 1 && <RewriteTab report={report} />}
        {tab === 2 && <RoadmapTab report={report} />}
        {tab === 3 && <InterviewTab report={report} />}
        {tab === 4 && <SourcesTab report={report} />}
      </div>
    </div>
  )
}

// ── Metric Card ──────────────────────────────
function MetricCard({ label, value, color, sub }) {
  return (
    <div style={s.metricCard}>
      <div style={s.metricLabel}>{label}</div>
      <div style={{ ...s.metricValue, color }}>{value}</div>
      <div style={s.metricSub}>{sub}</div>
    </div>
  )
}

// ── ATS Bar ──────────────────────────────────
function AtsBar({ label, score, color }) {
  return (
    <div style={s.atsBar}>
      <div style={s.atsBarMeta}>
        <span style={s.atsBarLabel}>{label}</span>
        <span style={{ ...s.atsBarScore, color }}>{score}/100</span>
      </div>
      <div style={s.atsTrack}>
        <div style={{ ...s.atsFill, width: `${score}%`, background: color }} />
      </div>
    </div>
  )
}

// ── Tab: Gaps ────────────────────────────────
function GapsTab({ report, allGaps }) {
  return (
    <div>
      {/* Strengths */}
      {report.strengths?.length > 0 && (
        <div style={s.section}>
          <div style={s.sectionTitle}>Your strengths</div>
          <div style={s.chips}>
            {report.strengths.map((sk, i) => (
              <span key={i} style={s.strengthChip}>{sk}</span>
            ))}
          </div>
        </div>
      )}

      {/* Quick wins */}
      {report.quick_wins?.length > 0 && (
        <div style={{ ...s.infoBox, marginBottom: '24px' }}>
          <span style={s.infoIcon}>⚡</span>
          <div>
            <div style={s.infoTitle}>Quick wins — do this week</div>
            <div style={s.infoText}>{report.quick_wins.join(' · ')}</div>
          </div>
        </div>
      )}

      {/* Gaps */}
      <div style={s.sectionTitle}>Skill gaps — ranked by priority</div>
      {allGaps.length === 0 ? (
        <div style={s.emptyState}>No major skill gaps found — great match!</div>
      ) : (
        allGaps.map((gap, i) => <GapCard key={i} gap={gap} />)
      )}

      {/* Summary */}
      {report.candidate_summary && (
        <div style={{ ...s.infoBox, marginTop: '24px', background: 'rgba(124,108,250,0.06)', borderColor: 'rgba(124,108,250,0.2)' }}>
          <span style={s.infoIcon}>💬</span>
          <div>
            <div style={s.infoTitle}>Career coach assessment</div>
            <div style={s.infoText}>{report.candidate_summary}</div>
          </div>
        </div>
      )}
    </div>
  )
}

function GapCard({ gap }) {
  const p = gap.priority || 'good_to_have'
  const colors = {
    critical:    { bg: 'rgba(248,113,113,0.08)', border: 'rgba(248,113,113,0.25)', dot: 'var(--red)', label: 'Critical' },
    important:   { bg: 'rgba(251,191,36,0.08)',  border: 'rgba(251,191,36,0.25)',  dot: 'var(--amber)', label: 'Important' },
    good_to_have:{ bg: 'rgba(52,211,153,0.06)',  border: 'rgba(52,211,153,0.2)',   dot: 'var(--green)', label: 'Nice to have' },
  }
  const c = colors[p] || colors.good_to_have
  const res = gap.free_resource || {}

  return (
    <div style={{ ...s.gapCard, background: c.bg, borderColor: c.border }}>
      <div style={s.gapTop}>
        <div style={s.gapName}>{gap.name}</div>
        <span style={{ ...s.priorityBadge, color: c.dot, borderColor: c.border }}>
          <span style={{ color: c.dot }}>●</span> {c.label}
        </span>
      </div>
      <div style={s.gapReason}>{gap.reason}</div>
      <div style={s.gapMeta}>
        <span style={s.gapTime}>⏱ {gap.estimated_learning_time || '—'}</span>
        {res.name && res.url && res.url.startsWith('http') && (
          <a href={res.url} target="_blank" rel="noreferrer" style={s.gapLink}>
            📚 {res.name} →
          </a>
        )}
        {res.name && (!res.url || !res.url.startsWith('http')) && (
          <span style={s.gapLinkText}>📚 {res.name}</span>
        )}
      </div>
    </div>
  )
}

// ── Tab: Rewrite ─────────────────────────────
function RewriteTab({ report }) {
  return (
    <div>
      {report.resume_summary && (
        <div style={s.section}>
          <div style={s.sectionTitle}>Professional summary</div>
          <div style={s.summaryBox}>{report.resume_summary}</div>
        </div>
      )}
      <div style={s.sectionTitle}>Bullet point rewrites</div>
      {(report.rewritten_bullets || []).length === 0 && (
        <div style={s.emptyState}>No rewrites generated.</div>
      )}
      {(report.rewritten_bullets || []).map((b, i) => (
        <div key={i} style={s.bulletCard}>
          <div style={s.bulletBefore}>
            <span style={s.bulletTag}>Before</span>
            <span style={s.bulletBeforeText}>{b.original}</span>
          </div>
          <div style={s.bulletArrow}>↓</div>
          <div style={s.bulletAfter}>
            <span style={s.bulletTagGreen}>After</span>
            <span style={s.bulletAfterText}>{b.rewritten}</span>
          </div>
          {(b.improvement_reason || b.keywords_added?.length > 0) && (
            <div style={s.bulletMeta}>
              {b.improvement_reason && <span style={s.bulletWhy}>💡 {b.improvement_reason}</span>}
              {b.keywords_added?.length > 0 && (
                <span style={s.bulletKeys}>
                  🔑 {b.keywords_added.join(', ')}
                </span>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

// ── Tab: Roadmap ─────────────────────────────
function RoadmapTab({ report }) {
  const roadmap = report.learning_roadmap || []
  const [expandedWeeks, setExpandedWeeks] = useState({})

  if (roadmap.length === 0) return <div style={s.emptyState}>No roadmap generated.</div>

  const toggleWeek = (weekIndex) => {
    setExpandedWeeks(prev => ({
      ...prev,
      [weekIndex]: !prev[weekIndex]
    }))
  }

  return (
    <div>
      <div style={s.sectionTitle}>Week by week learning roadmap</div>
      {roadmap.map((week, i) => {
        const isExpanded = expandedWeeks[i]
        return (
          <div key={i} style={{ ...s.weekCard, ...(isExpanded ? s.weekCardOpen : {}) }}>
            <button 
              style={s.weekHeaderBtn}
              onClick={() => toggleWeek(i)}
            >
              <div style={s.weekLeft}>
                <span style={s.weekNum}>Week {week.week}</span>
                <span style={s.weekFocus}>{week.focus}</span>
                {week.duration_hours && <span style={s.durationBadge}>{week.duration_hours}h</span>}
              </div>
              <div style={s.weekRight}>
                {(week.skills || []).slice(0, 3).map((sk, j) => (
                  <span key={j} style={s.skillChip}>{sk}</span>
                ))}
                <span style={{ ...s.expandIcon, transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)' }}>▼</span>
              </div>
            </button>
            
            {isExpanded && (
              <div style={s.weekBody}>
                <div style={s.weekGoal}><strong>📍 Goal:</strong> {week.goal}</div>
                
                {week.daily_plan?.length > 0 && (
                  <div style={s.dailyPlan}>
                    <div style={s.weekResTitle}>📅 Daily Plan:</div>
                    {week.daily_plan.map((day, j) => (
                      <div key={j} style={s.dayItem}>
                        <span style={s.dayDot}>•</span>
                        <span>{day}</span>
                      </div>
                    ))}
                  </div>
                )}

                {week.resources?.length > 0 && (
                  <div style={s.weekResources}>
                    <div style={s.weekResTitle}>🔗 Resources:</div>
                    {week.resources.map((r, j) => {
                      if (typeof r === 'object' && r.url) {
                        return (
                          <div key={j} style={s.resourceItem}>
                            <div style={s.resHeader}>
                              <a href={r.url} target="_blank" rel="noreferrer" style={s.resLink}>
                                {r.name}
                              </a>
                              <span style={s.resType}>{r.type}</span>
                              {r.free && <span style={s.freeBadge}>FREE</span>}
                            </div>
                            {r.duration && <div style={s.resDuration}>⏱️ {r.duration}</div>}
                          </div>
                        )
                      }
                      return (
                        <div key={j} style={s.weekRes}>
                          {typeof r === 'string' && r.startsWith('http')
                            ? <a href={r} target="_blank" rel="noreferrer" style={s.resLink}>{r}</a>
                            : <span style={s.resText}>{r}</span>
                          }
                        </div>
                      )
                    })}
                  </div>
                )}

                {week.practice_project && (
                  <div style={s.projectSection}>
                    <div style={s.weekResTitle}>🎯 Practice Project:</div>
                    <div style={s.projectText}>{week.practice_project}</div>
                  </div>
                )}

                {week.success_criteria && (
                  <div style={s.criteriaSection}>
                    <div style={s.weekResTitle}>✅ Success Criteria:</div>
                    {Array.isArray(week.success_criteria) 
                      ? week.success_criteria.map((c, j) => (
                          <div key={j} style={s.criteriaItem}>
                            <span style={s.checkmark}>✓</span> {c}
                          </div>
                        ))
                      : <div style={s.criteriaItem}>{week.success_criteria}</div>
                    }
                  </div>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

// ── Tab: Interview ───────────────────────────
function InterviewTab({ report }) {
  const questions = report.interview_questions || []
  const catColors = {
    technical:   { color: '#60a5fa', bg: 'rgba(96,165,250,0.1)'  },
    behavioral:  { color: '#c084fc', bg: 'rgba(192,132,252,0.1)' },
    situational: { color: 'var(--amber)', bg: 'rgba(251,191,36,0.1)' },
  }

  if (questions.length === 0) return <div style={s.emptyState}>No questions generated.</div>

  return (
    <div>
      <div style={s.sectionTitle}>Predicted interview questions</div>
      {questions.map((q, i) => {
        const c = catColors[q.category] || { color: 'var(--muted)', bg: 'var(--bg3)' }
        return (
          <div key={i} style={s.qCard}>
            <div style={s.qTop}>
              <span style={s.qNum}>Q{i + 1}</span>
              <span style={{ ...s.qCat, color: c.color, background: c.bg }}>{q.category}</span>
            </div>
            <div style={s.qText}>{q.question}</div>
            {q.why_asked && <div style={s.qWhy}>Why asked: {q.why_asked}</div>}
            {q.tip && (
              <div style={s.qTip}>
                <span style={{ color: 'var(--accent2)' }}>💡 Tip:</span> {q.tip}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

// ── Tab: Sources ─────────────────────────────
function SourcesTab({ report }) {
  const sources = report.sources || []
  return (
    <div>
      <div style={s.sectionTitle}>Market research sources</div>
      <p style={s.sourcesSub}>
        These sources were searched in real-time to determine current skill demand for your target role.
      </p>
      {sources.length === 0 ? (
        <div style={s.emptyState}>No sources collected.</div>
      ) : (
        <div style={s.sourcesGrid}>
          {sources.map((src, i) => {
            const isUrl = src.startsWith('http')
            const domain = isUrl ? src.split('/')[2]?.replace('www.', '') : src
            return (
              <div key={i} style={s.sourceCard}>
                <div style={s.sourceDomain}>{domain}</div>
                {isUrl && (
                  <a href={src} target="_blank" rel="noreferrer" style={s.sourceLink}>
                    View source →
                  </a>
                )}
              </div>
            )
          })}
        </div>
      )}
      <div style={s.confSection}>
        <div style={s.confLabel}>Agent confidence score</div>
        <div style={s.confValue}>
          {Math.round((report.confidence_score || 0) * 100)}%
        </div>
        <div style={s.confBar}>
          <div style={{
            ...s.confFill,
            width: `${Math.round((report.confidence_score || 0) * 100)}%`
          }} />
        </div>
        <div style={s.confSub}>
          Self-reflection quality score from the orchestrator
        </div>
      </div>
    </div>
  )
}

// ── Styles ───────────────────────────────────
const s = {
  candHeader: {
    display: 'flex', alignItems: 'center', gap: '16px',
    marginBottom: '32px',
    background: 'var(--bg2)', border: '1.5px solid var(--border-section)',
    borderRadius: 'var(--radius)', padding: '20px 24px',
    boxShadow: '0 0 1px rgba(255,255,255,0.08) inset',
  },
  avatar: {
    width: '48px', height: '48px', borderRadius: '50%',
    background: 'linear-gradient(135deg, var(--accent), #9333ea)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontFamily: 'var(--font-head)', fontWeight: 700, fontSize: '18px',
    color: '#fff', flexShrink: 0,
  },
  candName: { fontFamily: 'var(--font-head)', fontSize: '20px', fontWeight: 700, color: 'var(--text)' },
  candSub: { fontSize: '13px', color: 'var(--muted)', marginTop: '3px' },
  confBadge: {
    marginLeft: 'auto', fontSize: '12px', color: 'var(--muted)',
    background: 'var(--bg3)', border: '1px solid var(--border)',
    padding: '6px 14px', borderRadius: '20px',
  },
  metrics: {
    display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)',
    gap: '12px', marginBottom: '24px',
  },
  metricCard: {
    background: 'var(--bg2)', border: '1.5px solid var(--border-section)',
    borderRadius: 'var(--radius)', padding: '20px',
    boxShadow: '0 0 1px rgba(255,255,255,0.08) inset',
  },
  metricLabel: { fontSize: '11px', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '10px' },
  metricValue: { fontFamily: 'var(--font-head)', fontSize: '28px', fontWeight: 700, lineHeight: 1 },
  metricSub: { fontSize: '11px', color: 'var(--muted)', marginTop: '6px' },
  atsSection: {
    background: 'var(--bg2)', border: '1.5px solid var(--border-section)',
    borderRadius: 'var(--radius)', padding: '20px 24px',
    marginBottom: '28px',
    boxShadow: '0 0 1px rgba(255,255,255,0.08) inset',
  },
  atsSectionTitle: {
    fontFamily: 'var(--font-head)', fontSize: '13px', fontWeight: 600,
    color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em',
    marginBottom: '16px',
  },
  atsBars: { display: 'flex', flexDirection: 'column', gap: '14px' },
  atsBar: {},
  atsBarMeta: { display: 'flex', justifyContent: 'space-between', marginBottom: '6px' },
  atsBarLabel: { fontSize: '13px', color: 'var(--muted)' },
  atsBarScore: { fontSize: '13px', fontWeight: 600 },
  atsTrack: { height: '6px', background: 'var(--bg3)', borderRadius: '3px', overflow: 'hidden' },
  atsFill: { height: '100%', borderRadius: '3px', transition: 'width 1s ease' },
  tabsRow: {
    display: 'flex', gap: '4px', marginBottom: '24px',
    borderBottom: '1px solid var(--border)', paddingBottom: '0',
  },
  tabBtn: {
    display: 'flex', alignItems: 'center', gap: '6px',
    background: 'transparent', border: 'none', cursor: 'pointer',
    fontFamily: 'var(--font-body)', fontSize: '14px', color: '#ffffff',
    padding: '10px 16px', borderRadius: '8px 8px 0 0',
    borderBottom: '2px solid transparent', transition: 'all 0.2s',
    marginBottom: '-1px',
  },
  tabActive: { color: '#ffffff', borderBottomColor: 'var(--accent)' },
  tabBadge: {
    background: 'var(--red)', color: '#ffffff',
    fontSize: '10px', fontWeight: 700,
    padding: '1px 6px', borderRadius: '10px',
  },
  tabContent: {
    background: 'var(--bg2)', border: '1.5px solid var(--border-section)',
    borderRadius: 'var(--radius)', padding: '28px',
    minHeight: '300px',
    boxShadow: '0 0 1px rgba(255,255,255,0.08) inset',
  },
  section: { marginBottom: '28px' },
  sectionTitle: {
    fontFamily: 'var(--font-head)', fontSize: '14px', fontWeight: 600,
    color: 'var(--text)', marginBottom: '14px',
    textTransform: 'uppercase', letterSpacing: '0.05em',
  },
  chips: { display: 'flex', flexWrap: 'wrap', gap: '8px' },
  strengthChip: {
    fontSize: '13px', color: 'var(--green)',
    background: 'rgba(52,211,153,0.1)', border: '1px solid rgba(52,211,153,0.2)',
    padding: '5px 12px', borderRadius: '20px',
  },
  infoBox: {
    display: 'flex', alignItems: 'flex-start', gap: '12px',
    background: 'rgba(52,211,153,0.06)', border: '1px solid rgba(52,211,153,0.15)',
    borderRadius: 'var(--radius-sm)', padding: '14px 16px',
  },
  infoIcon: { fontSize: '18px', flexShrink: 0 },
  infoTitle: { fontSize: '13px', fontWeight: 600, color: 'var(--text)', marginBottom: '4px' },
  infoText: { fontSize: '13px', color: 'var(--muted)', lineHeight: 1.6 },
  gapCard: {
    border: '1.5px solid', borderRadius: 'var(--radius-sm)',
    padding: '16px', marginBottom: '10px',
    boxShadow: '0 0 1px rgba(255,255,255,0.08) inset',
  },
  gapTop: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' },
  gapName: { fontWeight: 600, fontSize: '15px', color: 'var(--text)' },
  priorityBadge: {
    fontSize: '11px', padding: '3px 10px', borderRadius: '20px',
    border: '1px solid', display: 'flex', alignItems: 'center', gap: '5px',
  },
  gapReason: { fontSize: '13px', color: 'var(--muted)', lineHeight: 1.5, marginBottom: '10px' },
  gapMeta: { display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' },
  gapTime: { fontSize: '12px', color: 'var(--muted)' },
  gapLink: { fontSize: '12px', color: 'var(--accent2)', textDecoration: 'none' },
  gapLinkText: { fontSize: '12px', color: 'var(--muted)' },
  emptyState: {
    textAlign: 'center', padding: '48px',
    color: 'var(--muted)', fontSize: '14px',
  },
  summaryBox: {
    background: 'rgba(124,108,250,0.06)', border: '1px solid rgba(124,108,250,0.2)',
    borderRadius: 'var(--radius-sm)', padding: '16px',
    fontSize: '14px', color: 'var(--text)', lineHeight: 1.7,
    marginBottom: '24px',
  },
  bulletCard: {
    background: 'var(--bg3)', borderRadius: 'var(--radius-sm)',
    padding: '16px', marginBottom: '14px',
    border: '1px solid var(--border)',
  },
  bulletBefore: { display: 'flex', gap: '10px', alignItems: 'flex-start', marginBottom: '6px' },
  bulletTag: {
    fontSize: '10px', fontWeight: 700, flexShrink: 0,
    background: 'rgba(248,113,113,0.15)', color: 'var(--red)',
    padding: '2px 8px', borderRadius: '4px', marginTop: '2px',
  },
  bulletTagGreen: {
    fontSize: '10px', fontWeight: 700, flexShrink: 0,
    background: 'rgba(52,211,153,0.15)', color: 'var(--green)',
    padding: '2px 8px', borderRadius: '4px', marginTop: '2px',
  },
  bulletBeforeText: { fontSize: '13px', color: 'var(--muted)', textDecoration: 'line-through', lineHeight: 1.5 },
  bulletArrow: { textAlign: 'center', fontSize: '16px', color: 'var(--border2)', margin: '4px 0' },
  bulletAfter: { display: 'flex', gap: '10px', alignItems: 'flex-start', marginBottom: '8px' },
  bulletAfterText: { fontSize: '13px', color: 'var(--text)', lineHeight: 1.5, fontWeight: 500 },
  bulletMeta: { display: 'flex', gap: '16px', flexWrap: 'wrap', borderTop: '1px solid var(--border)', paddingTop: '8px', marginTop: '4px' },
  bulletWhy: { fontSize: '12px', color: 'var(--muted)' },
  bulletKeys: { fontSize: '12px', color: 'var(--accent2)' },
  weekCard: {
    border: '1.5px solid var(--border-section)', borderRadius: 'var(--radius-sm)',
    marginBottom: '8px', overflow: 'hidden', transition: 'border-color 0.2s',
    boxShadow: '0 0 1px rgba(255,255,255,0.08) inset',
  },
  weekCardOpen: { borderColor: 'rgba(124,108,250,0.3)' },
  weekHeaderBtn: {
    width: '100%', background: 'transparent', border: 'none',
    padding: '16px 18px',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    gap: '12px', cursor: 'pointer', transition: 'background 0.2s',
  },
  weekHeader: {
    width: '100%', background: 'transparent', border: 'none',
    padding: '16px 18px',
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    gap: '12px',
  },
  weekLeft: { display: 'flex', alignItems: 'center', gap: '14px', flex: 1 },
  weekNum: {
    fontSize: '11px', fontWeight: 700, color: 'var(--accent2)',
    background: 'rgba(124,108,250,0.1)', padding: '3px 10px',
    borderRadius: '4px', whiteSpace: 'nowrap',
  },
  weekFocus: { fontSize: '14px', fontWeight: 600, color: 'var(--text)' },
  durationBadge: {
    fontSize: '11px', fontWeight: 600, color: 'var(--green)',
    background: 'rgba(34,197,94,0.1)', padding: '2px 8px',
    borderRadius: '4px', whiteSpace: 'nowrap',
  },
  weekRight: { display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 },
  skillChip: {
    fontSize: '11px', color: 'var(--muted)',
    background: 'var(--bg3)', border: '1px solid var(--border)',
    padding: '2px 8px', borderRadius: '4px',
  },
  expandIcon: {
    fontSize: '12px', color: 'var(--accent2)', transition: 'transform 0.3s ease',
    marginLeft: 'auto', display: 'flex', alignItems: 'center',
  },
  weekBody: {
    padding: '0 18px 18px',
    borderTop: '1px solid var(--border)',
    paddingTop: '14px',
  },
  weekGoal: { 
    fontSize: '13px', color: 'var(--text)', lineHeight: 1.6, 
    marginBottom: '14px', padding: '10px 12px',
    background: 'rgba(124,108,250,0.05)', borderRadius: '6px',
  },
  dailyPlan: {
    marginBottom: '14px', paddingBottom: '14px', borderBottom: '1px solid var(--border)',
  },
  dayItem: {
    display: 'flex', gap: '10px', fontSize: '13px', 
    color: 'var(--muted)', marginBottom: '6px', lineHeight: 1.5,
  },
  dayDot: { color: 'var(--accent2)', fontWeight: 'bold', minWidth: '8px' },
  weekResources: {
    marginBottom: '14px', paddingBottom: '14px', borderBottom: '1px solid var(--border)',
  },
  weekResTitle: { 
    fontSize: '12px', color: 'var(--muted)', marginBottom: '8px', 
    fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em',
  },
  resourceItem: {
    marginBottom: '10px', padding: '10px 12px',
    background: 'var(--bg3)', borderRadius: '6px',
  },
  resHeader: {
    display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap',
    marginBottom: '4px',
  },
  resLink: { 
    fontSize: '13px', color: 'var(--accent2)', fontWeight: 500,
    textDecoration: 'none', flex: 1,
  },
  resType: {
    fontSize: '10px', color: 'var(--muted)', background: 'var(--bg2)',
    padding: '2px 6px', borderRadius: '3px', whiteSpace: 'nowrap',
  },
  freeBadge: {
    fontSize: '10px', fontWeight: 700, color: 'var(--green)',
    background: 'rgba(34,197,94,0.15)', padding: '2px 6px', borderRadius: '3px',
  },
  resDuration: {
    fontSize: '11px', color: 'var(--muted)', marginLeft: '0',
  },
  weekRes: { marginBottom: '6px' },
  resText: { fontSize: '12px', color: 'var(--muted)' },
  projectSection: {
    marginBottom: '14px', paddingBottom: '14px', borderBottom: '1px solid var(--border)',
  },
  projectText: {
    fontSize: '13px', color: 'var(--text)', lineHeight: 1.6,
    padding: '10px 12px', background: 'rgba(251,191,36,0.05)', borderRadius: '6px',
  },
  criteriaSection: {
    marginBottom: '0',
  },
  criteriaItem: {
    display: 'flex', gap: '10px', fontSize: '13px', 
    color: 'var(--text)', marginBottom: '6px', lineHeight: 1.5,
  },
  checkmark: { color: 'var(--green)', fontWeight: 'bold', minWidth: '12px' },
  qCard: {
    background: 'var(--bg3)', border: '1.5px solid var(--border-section)',
    borderRadius: 'var(--radius-sm)', padding: '18px',
    marginBottom: '12px',
    boxShadow: '0 0 1px rgba(255,255,255,0.08) inset',
  },
  qTop: { display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px' },
  qNum: {
    fontFamily: 'var(--font-head)', fontSize: '13px', fontWeight: 700,
    color: 'var(--accent2)',
  },
  qCat: {
    fontSize: '11px', padding: '2px 10px', borderRadius: '20px', fontWeight: 500,
  },
  qText: { fontSize: '14px', color: 'var(--text)', fontWeight: 500, lineHeight: 1.6, marginBottom: '8px' },
  qWhy: { fontSize: '12px', color: 'var(--muted)', marginBottom: '6px' },
  qTip: { fontSize: '12px', color: 'var(--muted)', lineHeight: 1.5 },
  sourcesSub: { fontSize: '13px', color: 'var(--muted)', marginBottom: '20px', lineHeight: 1.6 },
  sourcesGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '10px', marginBottom: '28px' },
  sourceCard: {
    background: 'var(--bg3)', border: '1.5px solid var(--border-section)',
    borderRadius: 'var(--radius-sm)', padding: '14px',
    boxShadow: '0 0 1px rgba(255,255,255,0.08) inset',
  },
  sourceDomain: { fontSize: '13px', fontWeight: 500, color: 'var(--text)', marginBottom: '6px', wordBreak: 'break-all' },
  sourceLink: { fontSize: '12px', color: 'var(--accent2)' },
  confSection: {
    background: 'var(--bg3)', border: '1px solid var(--border)',
    borderRadius: 'var(--radius-sm)', padding: '20px',
  },
  confLabel: { fontSize: '12px', color: 'var(--muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.06em' },
  confValue: { fontFamily: 'var(--font-head)', fontSize: '36px', fontWeight: 700, color: 'var(--text)', marginBottom: '12px' },
  confBar: { height: '4px', background: 'var(--bg2)', borderRadius: '2px', overflow: 'hidden', marginBottom: '10px' },
  confFill: { height: '100%', background: 'linear-gradient(90deg, var(--accent), var(--green))', borderRadius: '2px', transition: 'width 1s ease' },
  confSub: { fontSize: '12px', color: 'var(--muted)' },
}
