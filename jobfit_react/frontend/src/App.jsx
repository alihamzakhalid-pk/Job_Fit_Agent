import { useState, useRef, useCallback } from 'react'
import axios from 'axios'
import UploadSection from './components/UploadSection.jsx'
import Pipeline from './components/Pipeline.jsx'
import Dashboard from './components/Dashboard.jsx'

// API Configuration - Works for both local and production
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const STEPS = [
  { id: 'resume_parser',    label: 'Resume Parser',    desc: 'Extracting skills, experience, education' },
  { id: 'market_research',  label: 'Market Research',  desc: 'Searching 3 queries for live market demand' },
  { id: 'gap_analyzer',     label: 'Gap Analyzer',     desc: 'Comparing profile to market and job' },
  { id: 'resume_rewriter',  label: 'Resume Rewriter',  desc: 'Rewriting bullets and scoring ATS' },
  { id: 'self_reflection',  label: 'Self Reflection',  desc: 'Quality checking all outputs' },
]

export default function App() {
  const [file, setFile]                 = useState(null)
  const [jobDesc, setJobDesc]           = useState('')
  const [phase, setPhase]               = useState('input')   // input | running | done
  const [stepIndex, setStepIndex]       = useState(-1)
  const [completedSteps, setCompleted]  = useState([])
  const [report, setReport]             = useState(null)
  const [error, setError]               = useState(null)

  const handleAnalyze = useCallback(async () => {
    if (!file || !jobDesc.trim()) return
    setError(null)
    setPhase('running')
    setStepIndex(0)
    setCompleted([])

    // Animate through steps while waiting for API
    const stepTimer = setInterval(() => {
      setStepIndex(prev => {
        const next = prev + 1
        setCompleted(c => [...c, STEPS[prev]?.id])
        if (next >= STEPS.length) clearInterval(stepTimer)
        return next
      })
    }, 2200)

    try {
      const form = new FormData()
      form.append('resume', file)
      form.append('job_description', jobDesc)

      const res = await axios.post(`${API_BASE_URL}/analyze`, form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      clearInterval(stepTimer)
      setCompleted(STEPS.map(s => s.id))
      setStepIndex(STEPS.length)

      if (res.data.success) {
        setTimeout(() => {
          setReport(res.data.report)
          setPhase('done')
        }, 600)
      } else {
        setError(res.data.error || 'Something went wrong')
        setPhase('input')
      }
    } catch (err) {
      clearInterval(stepTimer)
      setError(err.response?.data?.error || err.message || 'Network error — is the backend running?')
      setPhase('input')
    }
  }, [file, jobDesc])

  const handleReset = () => {
    setFile(null)
    setJobDesc('')
    setPhase('input')
    setStepIndex(-1)
    setCompleted([])
    setReport(null)
    setError(null)
  }

  return (
    <div style={styles.root}>
      {/* Background grid */}
      <div style={styles.grid} />
      <div style={styles.glow1} />
      <div style={styles.glow2} />

      {/* Header */}
      <header style={styles.header} className="fade-up">
        <div style={styles.logo}>
          <span style={styles.logoDot} />
          <span style={styles.logoText}>JobFit<span style={styles.logoAccent}>Agent</span></span>
        </div>
        <div style={styles.badge}>Multi-Agent AI · Powered by LangGraph</div>
        {phase === 'done' && (
          <button style={styles.resetBtn} onClick={handleReset}>← New Analysis</button>
        )}
      </header>

      <main style={styles.main}>
        {phase === 'input' && (
          <UploadSection
            file={file}
            setFile={setFile}
            jobDesc={jobDesc}
            setJobDesc={setJobDesc}
            onAnalyze={handleAnalyze}
            error={error}
          />
        )}
        {phase === 'running' && (
          <Pipeline steps={STEPS} stepIndex={stepIndex} completedSteps={completedSteps} />
        )}
        {phase === 'done' && report && (
          <Dashboard report={report} />
        )}
      </main>
    </div>
  )
}

const styles = {
  root: {
    minHeight: '100vh',
    position: 'relative',
    overflowX: 'hidden',
  },
  grid: {
    position: 'fixed', inset: 0, zIndex: 0,
    backgroundImage: `linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px)`,
    backgroundSize: '48px 48px',
    pointerEvents: 'none',
  },
  glow1: {
    position: 'fixed', top: '-200px', left: '20%',
    width: '600px', height: '600px', borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(124,108,250,0.12) 0%, transparent 70%)',
    pointerEvents: 'none', zIndex: 0,
  },
  glow2: {
    position: 'fixed', bottom: '-200px', right: '10%',
    width: '500px', height: '500px', borderRadius: '50%',
    background: 'radial-gradient(circle, rgba(52,211,153,0.08) 0%, transparent 70%)',
    pointerEvents: 'none', zIndex: 0,
  },
  header: {
    position: 'relative', zIndex: 10,
    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
    padding: '24px 48px',
    borderBottom: '1px solid rgba(255,255,255,0.06)',
    backdropFilter: 'blur(12px)',
  },
  logo: { display: 'flex', alignItems: 'center', gap: '10px' },
  logoDot: {
    width: '10px', height: '10px', borderRadius: '50%',
    background: 'var(--accent)',
    boxShadow: '0 0 12px var(--accent)',
    animation: 'glow 2s ease-in-out infinite',
  },
  logoText: {
    fontFamily: 'var(--font-head)', fontSize: '20px',
    fontWeight: 700, color: 'var(--text)',
  },
  logoAccent: { color: 'var(--accent2)' },
  badge: {
    fontSize: '12px', color: '#ffffff',
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid var(--border)',
    padding: '6px 14px', borderRadius: '20px',
    letterSpacing: '0.02em',
  },
  resetBtn: {
    background: 'transparent', border: '1px solid var(--border2)',
    color: '#ffffff', padding: '8px 18px',
    borderRadius: '8px', cursor: 'pointer',
    fontFamily: 'var(--font-body)', fontSize: '13px',
    transition: 'all 0.2s',
  },
  main: {
    position: 'relative', zIndex: 5,
    maxWidth: '1100px', margin: '0 auto',
    padding: '48px 24px',
  },
}
