import React, { useRef, useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import BackgroundBlobs from '../components/BackgroundBlobs'

export default function AnalyzePage() {
    const { state } = useLocation()
    const navigate = useNavigate()
    const fileInputRef = useRef(null)

    const [file, setFile] = useState(state?.file || null)
    const [selectedDemoSample, setSelectedDemoSample] = useState(state?.demoSample || null)
    const [previewUrl, setPreviewUrl] = useState(null)
    const [isVideo, setIsVideo] = useState(false)
    const [analyzing, setAnalyzing] = useState(false)
    const [result, setResult] = useState(null)
    const [error, setError] = useState(null)

    // New state for Infant details
    const [infantId, setInfantId] = useState(localStorage.getItem('lastInfantId') || 'INF001')
    const [infantName, setInfantName] = useState('')
    const [infantAge, setInfantAge] = useState(0)

    // Pre-select demo sample if passed via router state or default to null
    useEffect(() => {
        if (state?.demoSample) {
            handleSelectDemo(state.demoSample)
        }
    }, [state?.demoSample])

    // Build preview URL whenever file changes
    useEffect(() => {
        if (!file) return
        const url = URL.createObjectURL(file)
        setPreviewUrl(url)
        setIsVideo(file.type.startsWith('video/'))
        setSelectedDemoSample(null)
        setResult(null)
        setError(null)
        return () => URL.revokeObjectURL(url)
    }, [file])

    const handleSelectDemo = (filename) => {
        setSelectedDemoSample(filename)
        setFile(null)
        setPreviewUrl(`http://127.0.0.1:8000/demo_samples/${filename}`)
        setIsVideo(true)
        setResult(null)
        setError(null)
    }

    const handleFileChange = (e) => {
        const picked = e.target.files[0]
        if (picked) {
            setFile(picked)
            setSelectedDemoSample(null)
        }
        e.target.value = ''
    }

    const handleAnalyze = async () => {
        if ((!file && !selectedDemoSample) || !infantId) {
            setError('Please provide an Infant ID and select a file or demo sample.')
            return
        }
        setAnalyzing(true)
        setResult(null)
        setError(null)

        try {
            // 1. Try to register the infant first (silent fail if exists)
            await fetch('http://127.0.0.1:8000/api/pain/infant', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    infant_id: infantId,
                    name: infantName || `Infant ${infantId}`,
                    age_days: parseInt(infantAge) || 0
                })
            }).catch(() => {}) // Ignore errors (e.g. 409 Conflict)

            // 2. Run prediction
            const formData = new FormData()
            formData.append('infant_id', infantId)
            if (selectedDemoSample) {
                formData.append('sample_name', selectedDemoSample)
            } else if (file) {
                formData.append('file', file)
            }

            const res = await fetch('http://127.0.0.1:8000/api/pain/predict', {
                method: 'POST',
                body: formData,
            })

            if (!res.ok) {
                const errData = await res.json()
                throw new Error(errData.detail || `Server error: ${res.status}`)
            }
            const data = await res.json()
            setResult(data)
            
            // Save last used infant ID to local storage for History/Report pages
            localStorage.setItem('lastInfantId', infantId)
        } catch (err) {
            setError(err.message || 'Analysis failed. Please try again.')
        } finally {
            setAnalyzing(false)
        }
    }

    const fileTypeLabel = selectedDemoSample
        ? 'Benchmark Sample (Direct)'
        : file
            ? file.type.startsWith('video/') ? 'Uploaded Video' : 'Uploaded Image'
            : null

    return (
        <div className="relative min-h-screen bg-[#e0f7ff] font-sans overflow-x-hidden">
            <BackgroundBlobs />
            <div className="relative z-10">
                <Navbar />

                {/* Hidden file input */}
                <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*,video/*"
                    className="hidden"
                    onChange={handleFileChange}
                />

                <div className="pt-32 pb-20 px-6">
                    <div className="max-w-6xl mx-auto">

                        {/* Header */}
                        <div className="mb-10 animate-slide-up">
                            <button
                                onClick={() => navigate('/')}
                                className="inline-flex items-center gap-2 text-indigo-600 font-bold text-sm mb-6 hover:gap-3 transition-all"
                            >
                                <svg viewBox="0 0 24 24" className="w-4 h-4 fill-none stroke-current stroke-2">
                                    <path d="M19 12H5M12 19l-7-7 7-7" />
                                </svg>
                                Back to Home
                            </button>
                            <h1 className="text-4xl md:text-5xl font-black text-[#1c2b4a] tracking-tight mb-2">
                                Infant Pain Analysis
                            </h1>
                            <div className="w-20 h-1.5 bg-indigo-600 rounded-full" />
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 animate-slide-up" style={{ animationDelay: '0.1s' }}>

                            {/* LEFT — Infant Details Form */}
                            <div className="bg-white/80 backdrop-blur-md rounded-[2rem] shadow-xl shadow-blue-900/5 border border-blue-50 p-8 flex flex-col gap-6">
                                <h2 className="text-lg font-bold text-[#1c2b4a] flex items-center gap-2">
                                    <span className="w-2 h-6 bg-indigo-600 rounded-full inline-block" />
                                    Patient Details
                                </h2>
                                
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-xs font-bold text-[#1c2b4a]/60 uppercase tracking-widest mb-2">Infant ID *</label>
                                        <input 
                                            type="text" 
                                            value={infantId}
                                            onChange={(e) => setInfantId(e.target.value)}
                                            placeholder="e.g. B101"
                                            className="w-full px-4 py-3 rounded-xl border border-indigo-100 bg-indigo-50/30 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-bold text-[#1c2b4a]"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-bold text-[#1c2b4a]/60 uppercase tracking-widest mb-2">Patient Name</label>
                                        <input 
                                            type="text" 
                                            value={infantName}
                                            onChange={(e) => setInfantName(e.target.value)}
                                            placeholder="Optional"
                                            className="w-full px-4 py-3 rounded-xl border border-indigo-100 bg-indigo-50/30 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-bold text-[#1c2b4a]"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-bold text-[#1c2b4a]/60 uppercase tracking-widest mb-2">Age (Days)</label>
                                        <input 
                                            type="number" 
                                            value={infantAge}
                                            onChange={(e) => setInfantAge(e.target.value)}
                                            className="w-full px-4 py-3 rounded-xl border border-indigo-100 bg-indigo-50/30 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-bold text-[#1c2b4a]"
                                        />
                                    </div>
                                </div>
                                <p className="text-[10px] text-[#1c2b4a]/40 font-bold italic">* Required to save to history</p>
                            </div>

                            {/* MIDDLE — Preview */}
                            <div className="bg-white rounded-[2rem] shadow-xl shadow-blue-900/5 border border-blue-50 p-8 flex flex-col gap-6">
                                <h2 className="text-lg font-bold text-[#1c2b4a] flex items-center justify-between">
                                    <span className="flex items-center gap-2">
                                        <span className="w-2 h-6 bg-indigo-600 rounded-full inline-block" />
                                        Media Review
                                    </span>
                                    <span className="text-[10px] font-bold text-indigo-700 bg-indigo-50 border border-indigo-200 px-2.5 py-1 rounded-full uppercase tracking-wider">
                                        Demo Samples Ready
                                    </span>
                                </h2>

                                {/* Quick Benchmark Selector */}
                                <div className="p-3.5 bg-gradient-to-r from-blue-50/70 to-indigo-50/50 rounded-2xl border border-indigo-100/80 flex flex-col gap-2.5">
                                    <div className="flex items-center justify-between">
                                        <span className="text-xs font-bold text-[#1c2b4a] flex items-center gap-1.5">
                                            <span className="w-2 h-2 rounded-full bg-indigo-600"></span>
                                            Use Direct Benchmark Video:
                                        </span>
                                        <span className="text-[10px] text-emerald-600 font-bold bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
                                            No Upload Copy
                                        </span>
                                    </div>
                                    <div className="grid grid-cols-2 gap-2">
                                        <button
                                            type="button"
                                            onClick={() => handleSelectDemo('S001_Pain_1_[0]_20s.mp4')}
                                            className={`px-3 py-2.5 rounded-xl border text-xs font-bold transition-all text-left flex flex-col gap-1 ${
                                                selectedDemoSample === 'S001_Pain_1_[0]_20s.mp4'
                                                    ? 'border-red-400 bg-red-50 text-red-700 shadow-sm ring-2 ring-red-400/30'
                                                    : 'border-slate-200 bg-white hover:border-red-300 text-slate-700'
                                            }`}
                                        >
                                            <span className="flex items-center gap-1.5 font-bold">
                                                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                                                Severe Pain Video
                                            </span>
                                            <span className="text-[10px] text-slate-400 font-mono truncate">
                                                S001_Pain_1_[0]_20s
                                            </span>
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => handleSelectDemo('S001_Rest_1_[0]_20s.mp4')}
                                            className={`px-3 py-2.5 rounded-xl border text-xs font-bold transition-all text-left flex flex-col gap-1 ${
                                                selectedDemoSample === 'S001_Rest_1_[0]_20s.mp4'
                                                    ? 'border-emerald-400 bg-emerald-50 text-emerald-700 shadow-sm ring-2 ring-emerald-400/30'
                                                    : 'border-slate-200 bg-white hover:border-emerald-300 text-slate-700'
                                            }`}
                                        >
                                            <span className="flex items-center gap-1.5 font-bold">
                                                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                                                Rest / Baseline Video
                                            </span>
                                            <span className="text-[10px] text-slate-400 font-mono truncate">
                                                S001_Rest_1_[0]_20s
                                            </span>
                                        </button>
                                    </div>
                                </div>

                                {previewUrl ? (
                                    <div className="relative rounded-2xl overflow-hidden bg-[#f0f7ff] flex items-center justify-center min-h-[260px] border border-blue-100">
                                        {isVideo ? (
                                            <video
                                                key={previewUrl}
                                                src={previewUrl}
                                                controls
                                                autoPlay
                                                muted
                                                className="w-full max-h-64 rounded-2xl object-contain"
                                            />
                                        ) : (
                                            <img
                                                src={previewUrl}
                                                alt="Uploaded infant"
                                                className="w-full max-h-64 object-contain rounded-2xl"
                                            />
                                        )}
                                        {fileTypeLabel && (
                                            <span className="absolute top-3 right-3 text-[10px] font-bold text-indigo-700 bg-white/90 backdrop-blur-sm border border-indigo-100 px-2.5 py-0.5 rounded-full uppercase tracking-wide shadow-sm">
                                                {fileTypeLabel}
                                            </span>
                                        )}
                                    </div>
                                ) : (
                                    <div
                                        onClick={() => fileInputRef.current?.click()}
                                        className="flex flex-col items-center justify-center gap-4 min-h-[260px] rounded-2xl border-2 border-dashed border-indigo-200 bg-indigo-50/30 cursor-pointer hover:bg-indigo-50 transition-colors"
                                    >
                                        <div className="w-16 h-16 rounded-2xl bg-indigo-100 flex items-center justify-center">
                                            <svg className="w-8 h-8 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                                <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                                            </svg>
                                        </div>
                                        <p className="text-sm font-semibold text-[#1c2b4a]/50 text-center px-4">
                                            Click to upload a custom video or select a benchmark sample above
                                        </p>
                                    </div>
                                )}

                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    className="w-full py-3 rounded-2xl border-2 border-indigo-200 text-indigo-600 font-bold text-sm hover:bg-indigo-50 transition-all flex items-center justify-center gap-2"
                                >
                                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                                    </svg>
                                    {file ? 'Change Uploaded File' : 'Browse Other Local Files'}
                                </button>
                            </div>

                            {/* RIGHT — Action + Result */}
                            <div className="flex flex-col gap-6">

                                {/* Run Analysis Card */}
                                <div className="bg-white rounded-[2rem] shadow-xl shadow-blue-900/5 border border-blue-50 p-8 flex flex-col gap-6">
                                    <h2 className="text-lg font-bold text-[#1c2b4a] flex items-center gap-2">
                                        <span className="w-2 h-6 bg-indigo-600 rounded-full inline-block" />
                                        Process
                                    </h2>
                                    <p className="text-sm text-[#1c2b4a]/60 font-medium leading-relaxed">
                                        Click <strong>Analyze</strong> to run temporal ResNet + Keras 3 inference on the media.
                                    </p>

                                    <button
                                        onClick={handleAnalyze}
                                        disabled={(!file && !selectedDemoSample) || !infantId || analyzing}
                                        className={`w-full py-4 rounded-2xl font-bold text-sm transition-all flex items-center justify-center gap-2
                                            ${(!file && !selectedDemoSample) || !infantId || analyzing
                                                ? 'bg-[#1c2b4a]/10 text-[#1c2b4a]/30 cursor-not-allowed'
                                                : 'bg-[#1c2b4a] text-white hover:bg-[#2a3c5e] hover:-translate-y-0.5 shadow-lg shadow-indigo-200 active:scale-95'
                                            }`}
                                    >
                                        {analyzing ? (
                                            <>
                                                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                                                </svg>
                                                Running AI...
                                            </>
                                        ) : (
                                            <>
                                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                                    <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.347.347a3.5 3.5 0 01-4.95 0l-.347-.347z" />
                                                </svg>
                                                Start Analysis
                                            </>
                                        )}
                                    </button>
                                </div>

                                {/* Result Card */}
                                {(result || error) && (
                                    <div className={`rounded-[2rem] shadow-xl border p-8 animate-slide-up
                                        ${error
                                            ? 'bg-red-50 border-red-100'
                                            : 'bg-white border-blue-50 shadow-blue-900/5'
                                        }`}
                                    >
                                        {error ? (
                                            <>
                                                <h3 className="text-base font-bold text-red-600 mb-2">Error</h3>
                                                <p className="text-sm text-red-500 font-medium">{error}</p>
                                            </>
                                        ) : (
                                            <>
                                                <h3 className="text-base font-bold text-[#1c2b4a] mb-4 flex items-center gap-2">
                                                    <span className="w-2 h-5 bg-indigo-600 rounded-full inline-block" />
                                                    Diagnosis Result
                                                </h3>
                                                <div className="space-y-3">
                                                    <div className="flex justify-between items-center py-2 border-t border-blue-50">
                                                        <span className="text-xs font-bold text-[#1c2b4a]/50 uppercase tracking-widest">Pain Status</span>
                                                        <span className={`text-sm font-black px-3 py-1 rounded-full ${
                                                            result.pain_level.includes('No')
                                                                ? 'text-green-600 bg-green-50'
                                                                : result.pain_level.includes('Mild')
                                                                    ? 'text-amber-600 bg-amber-50'
                                                                    : 'text-red-600 bg-red-50'
                                                        }`}>{result.pain_level}</span>
                                                    </div>
                                                    <div className="flex justify-between items-center py-2 border-t border-blue-50">
                                                        <span className="text-xs font-bold text-[#1c2b4a]/50 uppercase tracking-widest">Pain Score</span>
                                                        <span className="text-sm font-black text-indigo-600">{(result.pain_score * 100).toFixed(1)}%</span>
                                                    </div>
                                                    <div className="flex justify-between items-center py-2 border-t border-blue-50">
                                                        <span className="text-xs font-bold text-[#1c2b4a]/50 uppercase tracking-widest">Confidence</span>
                                                        <span className="text-sm font-black text-indigo-600">{(result.confidence * 100).toFixed(1)}%</span>
                                                    </div>
                                                    {result.reason && (
                                                        <div className="py-2 border-t border-blue-50">
                                                            <span className="text-xs font-bold text-[#1c2b4a]/50 uppercase tracking-widest block mb-1">Clinical Observation</span>
                                                            <p className="text-xs text-[#1c2b4a]/80 font-medium bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                                                                {result.reason}
                                                            </p>
                                                        </div>
                                                    )}
                                                    {result.alert_created && (
                                                        <div className="bg-red-50 text-red-600 text-[10px] font-black uppercase text-center py-2 rounded-lg border border-red-100 mt-2">
                                                            ⚠️ Severe Pain Alert Triggered
                                                        </div>
                                                    )}
                                                </div>
                                            </>
                                        )}
                                    </div>
                                )}

                            </div>
                        </div>
                    </div>
                </div>

                <footer className="py-10 border-t border-gray-100 text-center">
                    <p className="text-gray-400 text-sm font-medium">© 2026 NeuralMedics Platform. Neonatal Care.</p>
                </footer>
            </div>
        </div>
    )
}
