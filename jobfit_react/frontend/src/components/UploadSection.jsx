import { useRef, useState } from 'react'

export default function UploadSection({ file, setFile, jobDesc, setJobDesc, onAnalyze, error }) {
  const inputRef = useRef()
  const [dragging, setDragging] = useState(false)
  const [jobDescWarning, setJobDescWarning] = useState('')

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f?.type === 'application/pdf') setFile(f)
  }

  // Validate job description input
  const validateJobDesc = (text) => {
    const trimmed = text.trim()
    
    if (trimmed.length === 0) {
      setJobDescWarning('')
      return
    }
    
    if (trimmed.length < 50) {
      setJobDescWarning('⚠ Job description too short (min 50 characters)')
      return
    }
    
    const wordCount = trimmed.split(/\s+/).length
    if (wordCount < 5) {
      setJobDescWarning('⚠ Job description must have at least 5 words')
      return
    }
    
    setJobDescWarning('')
  }

  const handleJobDescChange = (e) => {
    const text = e.target.value
    setJobDesc(text)
    validateJobDesc(text)
  }

  const canRun = file && jobDesc.trim().length >= 50 && !jobDescWarning

  return (
    <div>
      {/* Hero */}
      <div style={s.hero} className="fade-up">
        <div style={s.heroTag}>AI-Powered Career Intelligence</div>
        <h1 style={s.heroTitle}>
          Know exactly what it takes<br />
          <span style={s.heroAccent}>to get the job.</span>
        </h1>
        <p style={s.heroSub}>
          Upload your resume. Paste a job description. Our multi-agent AI analyzes
          market demand, finds your skill gaps, rewrites your bullets, and predicts
          your interview questions — in under 60 seconds.
        </p>
      </div>

      {/* Agents row */}
      <div style={s.agentsRow} className="fade-up-1">
        {['Resume Parser', 'Market Research', 'Gap Analyzer', 'ATS Optimizer', 'Self Reflection'].map((a, i) => (
          <div key={i} style={s.agentChip}>
            <span style={s.agentDot} />
            {a}
          </div>
        ))}
      </div>

      {/* Input grid */}
      <div style={s.grid} className="fade-up-2">
        {/* Upload */}
        <div style={s.card}>
          <div style={s.cardLabel}>
            <span style={s.labelIcon}>01</span>
            Upload Resume
          </div>
          <div
            style={{ ...s.dropzone, ...(dragging ? s.dropzoneActive : {}), ...(file ? s.dropzoneFilled : {}) }}
            onClick={() => inputRef.current.click()}
            onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
          >
            <input
              ref={inputRef} type="file" accept=".pdf"
              style={{ display: 'none' }}
              onChange={e => setFile(e.target.files[0])}
            />
            {file ? (
              <div style={s.fileInfo}>
                <div style={s.fileIcon}>PDF</div>
                <div>
                  <div style={s.fileName}>{file.name}</div>
                  <div style={s.fileSize}>{(file.size / 1024).toFixed(1)} KB · Ready</div>
                </div>
                <button style={s.removeBtn} onClick={e => { e.stopPropagation(); setFile(null) }}>✕</button>
              </div>
            ) : (
              <div style={s.dropContent}>
                <div style={s.dropIconWrap}>
                  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="12" y1="18" x2="12" y2="12"/>
                    <line x1="9" y1="15" x2="15" y2="15"/>
                  </svg>
                </div>
                <div style={s.dropTitle}>Drop your PDF here</div>
                <div style={s.dropSub}>or click to browse · PDF only</div>
              </div>
            )}
          </div>
        </div>

        {/* Job description */}
        <div style={s.card}>
          <div style={s.cardLabel}>
            <span style={s.labelIcon}>02</span>
            Job Description
          </div>
          <textarea
            style={s.textarea}
            placeholder="Paste the full job description here...&#10;&#10;Include requirements, responsibilities, and qualifications for the best analysis."
            value={jobDesc}
            onChange={handleJobDescChange}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
            <div style={s.charCount}>{jobDesc.length} characters</div>
            {jobDescWarning && <div style={{ fontSize: '12px', color: '#fca5a5' }}>{jobDescWarning}</div>}
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div style={s.error} className="fade-up">
          <span style={{ color: 'var(--red)' }}>⚠</span> {error}
        </div>
      )}

      {/* CTA */}
      <div style={s.ctaWrap} className="fade-up-3">
        <button
          style={{ ...s.cta, ...(canRun ? {} : s.ctaDisabled) }}
          onClick={onAnalyze}
          disabled={!canRun}
        >
          <span>Analyze My Fit</span>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12 5 19 12 12 19"/>
          </svg>
        </button>
        {!canRun && (
          <p style={s.ctaHint}>
            {!file && !jobDesc ? 'Upload resume and paste job description to begin'
            : !file ? 'Upload your PDF resume to continue'
            : jobDescWarning ? jobDescWarning
            : jobDesc.trim().length < 50 ? `Job description too short (min 50 chars, currently ${jobDesc.length})`
            : 'Please fix the errors above'}
          </p>
        )}
      </div>

      {/* Feature row */}
      <div style={s.features} className="fade-up-4">
        {[
          { icon: '⚡', title: 'Real-time market data', desc: '3 live web searches per analysis' },
          { icon: '🎯', title: 'ATS optimization', desc: 'Before & after scoring with metrics' },
          { icon: '🗺️', title: 'Learning roadmap', desc: 'Week-by-week plan to close gaps' },
          { icon: '❓', title: 'Interview prep', desc: 'Predicted questions with tips' },
        ].map((f, i) => (
          <div key={i} style={s.featureCard}>
            <div style={s.featureIcon}>{f.icon}</div>
            <div style={s.featureTitle}>{f.title}</div>
            <div style={s.featureDesc}>{f.desc}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

const s = {
  hero: { 
    textAlign: 'center', marginBottom: '60px',
    paddingTop: '20px',
  },
  heroTag: {
    display: 'inline-block',
    fontSize: '11px', letterSpacing: '0.12em', textTransform: 'uppercase',
    color: 'var(--accent)', background: 'linear-gradient(135deg, rgba(124,108,250,0.12) 0%, rgba(124,108,250,0.05) 100%)',
    border: '1px solid rgba(124,108,250,0.35)',
    padding: '8px 18px', borderRadius: '24px', marginBottom: '24px',
    fontWeight: 500,
  },
  heroTitle: {
    fontFamily: 'var(--font-head)',
    fontSize: 'clamp(42px, 6vw, 64px)',
    fontWeight: 900, lineHeight: 1.15,
    color: 'var(--text)', marginBottom: '24px',
    letterSpacing: '-0.015em',
  },
  heroAccent: {
    background: 'linear-gradient(125deg, #7c6cfa 0%, #34d399 100%)',
    WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
  },
  heroSub: {
    fontSize: '17px', color: 'var(--muted)',
    maxWidth: '600px', margin: '0 auto', lineHeight: 1.75,
    fontWeight: 400,
  },
  agentsRow: {
    display: 'flex', flexWrap: 'wrap', justifyContent: 'center',
    gap: '12px', marginBottom: '56px',
  },
  agentChip: {
    display: 'flex', alignItems: 'center', gap: '8px',
    fontSize: '13px', color: 'var(--text)',
    background: 'linear-gradient(135deg, rgba(124,108,250,0.08) 0%, rgba(52,211,153,0.08) 100%)',
    border: '1px solid rgba(255,255,255,0.08)',
    padding: '8px 16px', borderRadius: '24px',
    fontWeight: 500,
    transition: 'all 0.3s',
  },
  agentDot: {
    width: '7px', height: '7px', borderRadius: '50%',
    background: 'linear-gradient(135deg, var(--accent), var(--accent2))',
    display: 'block',
    boxShadow: '0 0 8px rgba(124,108,250,0.4)',
  },
  grid: {
    display: 'grid', gridTemplateColumns: '1fr 1fr',
    gap: '24px', marginBottom: '40px',
  },
  card: {
    background: 'linear-gradient(135deg, rgba(255,255,255,0.02) 0%, rgba(255,255,255,0.005) 100%)',
    border: '1.5px solid rgba(255,255,255,0.1)',
    borderRadius: '16px', padding: '28px',
    display: 'flex', flexDirection: 'column', gap: '16px',
    boxShadow: '0 8px 32px rgba(0,0,0,0.1), 0 0 1px rgba(255,255,255,0.1) inset',
    backdropFilter: 'blur(8px)',
    transition: 'all 0.3s ease',
  },
  cardLabel: {
    display: 'flex', alignItems: 'center', gap: '12px',
    fontFamily: 'var(--font-head)', fontSize: '15px',
    fontWeight: 700, color: 'var(--text)',
  },
  labelIcon: {
    fontSize: '12px', color: '#ffffff',
    background: 'linear-gradient(135deg, var(--accent), #9333ea)',
    padding: '5px 11px', borderRadius: '6px',
    fontFamily: 'var(--font-body)', fontWeight: 600,
  },
  dropzone: {
    border: '2px dashed rgba(124,108,250,0.3)', borderRadius: '14px',
    padding: '40px 24px', cursor: 'pointer', transition: 'all 0.3s ease',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    minHeight: '200px',
    background: 'linear-gradient(135deg, rgba(124,108,250,0.02) 0%, rgba(52,211,153,0.02) 100%)',
  },
  dropzoneActive: {
    borderColor: 'var(--accent)', background: 'rgba(124,108,250,0.08)',
    boxShadow: '0 0 20px rgba(124,108,250,0.2)',
  },
  dropzoneFilled: {
    borderColor: 'var(--green)', borderStyle: 'solid',
    background: 'rgba(52,211,153,0.06)',
    boxShadow: '0 0 15px rgba(52,211,153,0.15)',
  },
  dropContent: { textAlign: 'center' },
  dropIconWrap: {
    width: '64px', height: '64px',
    background: 'linear-gradient(135deg, rgba(124,108,250,0.15) 0%, rgba(52,211,153,0.1) 100%)',
    borderRadius: '14px',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    margin: '0 auto 18px', color: 'var(--accent)',
    border: '1px solid rgba(124,108,250,0.2)',
  },
  dropTitle: { fontSize: '16px', color: 'var(--text)', fontWeight: 600, marginBottom: '8px' },
  dropSub: { fontSize: '13px', color: 'var(--muted)' },
  fileInfo: {
    display: 'flex', alignItems: 'center', gap: '16px', width: '100%',
  },
  fileIcon: {
    fontSize: '12px', fontWeight: 700,
    background: 'linear-gradient(135deg, rgba(124,108,250,0.2) 0%, rgba(124,108,250,0.1) 100%)',
    color: 'var(--accent)',
    border: '1px solid rgba(124,108,250,0.3)',
    padding: '8px 12px', borderRadius: '8px', flexShrink: 0,
  },
  fileName: { fontSize: '15px', color: 'var(--text)', fontWeight: 600, wordBreak: 'break-all' },
  fileSize: { fontSize: '13px', color: 'var(--green)', marginTop: '4px', fontWeight: 500 },
  removeBtn: {
    marginLeft: 'auto', background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.1)', color: 'var(--muted)',
    width: '32px', height: '32px', borderRadius: '8px',
    cursor: 'pointer', fontSize: '13px', flexShrink: 0,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    transition: 'all 0.2s',
  },
  textarea: {
    flex: 1, background: 'rgba(0,0,0,0.2)',
    border: '1.5px solid rgba(255,255,255,0.08)',
    borderRadius: '12px', color: 'var(--text)',
    fontFamily: 'var(--font-body)', fontSize: '15px',
    padding: '16px 18px', resize: 'none', outline: 'none',
    lineHeight: 1.7, minHeight: '220px',
    transition: 'all 0.3s ease',
  },
  charCount: { fontSize: '12px', color: 'var(--muted)', textAlign: 'right', fontWeight: 500 },
  error: {
    background: 'linear-gradient(135deg, rgba(248,113,113,0.1) 0%, rgba(248,113,113,0.05) 100%)',
    border: '1.5px solid rgba(248,113,113,0.25)',
    borderRadius: '12px', padding: '16px 20px',
    fontSize: '14px', color: '#fca5a5', marginBottom: '24px',
    display: 'flex', alignItems: 'center', gap: '10px',
  },
  ctaWrap: { display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '14px', marginTop: '12px' },
  cta: {
    display: 'flex', alignItems: 'center', gap: '11px',
    background: 'linear-gradient(135deg, #7c6cfa 0%, #9333ea 100%)',
    color: '#ffffff', border: 'none', borderRadius: '14px',
    padding: '18px 48px', fontSize: '16px', fontWeight: 700,
    fontFamily: 'var(--font-head)', cursor: 'pointer',
    transition: 'all 0.3s ease',
    boxShadow: '0 8px 32px rgba(124,108,250,0.4), 0 0 1px rgba(255,255,255,0.3) inset',
  },
  ctaDisabled: {
    background: 'linear-gradient(135deg, rgba(124,108,250,0.2) 0%, rgba(124,108,250,0.1) 100%)',
    color: 'rgba(255,255,255,0.5)',
    boxShadow: 'none', cursor: 'not-allowed',
  },
  ctaHint: { fontSize: '13px', color: 'var(--muted)', fontWeight: 500 },
  features: {
    display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '18px', marginTop: '64px',
  },
  featureCard: {
    background: 'linear-gradient(135deg, rgba(255,255,255,0.02) 0%, rgba(255,255,255,0.005) 100%)',
    border: '1.5px solid rgba(255,255,255,0.08)',
    borderRadius: '14px', padding: '24px',
    transition: 'all 0.3s ease',
    boxShadow: '0 0 1px rgba(255,255,255,0.08) inset',
  },
  featureIcon: { fontSize: '28px', marginBottom: '12px' },
  featureTitle: {
    fontSize: '14px', fontWeight: 700,
    color: 'var(--text)', marginBottom: '8px',
  },
  featureDesc: { fontSize: '13px', color: 'var(--muted)', lineHeight: 1.6, fontWeight: 500 },
}
