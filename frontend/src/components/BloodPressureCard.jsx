import React, { useState, useEffect } from 'react'

const initialBars = [
    { id: 'EyeL', h: 85, color: '#93c5fd' },
    { id: 'EyeR', h: 88, color: '#93c5fd' },
    { id: 'Nose', h: 95, color: '#1c2b4a' },
    { id: 'Mth', h: 92, color: '#60a5fa' },
    { id: 'Jaw', h: 75, color: '#93c5fd' },
    { id: 'BrwL', h: 82, color: '#93c5fd' },
    { id: 'BrwR', h: 80, color: '#bfdbfe' },
    { id: 'Chk', h: 78, color: '#bfdbfe' },
]

export default function BloodPressureCard() {
    const [bars, setBars] = useState(initialBars)
    const [overallConfidence, setOverallConfidence] = useState(87)
    const [latestScan, setLatestScan] = useState(null)
    const [infantId, setInfantId] = useState('')

    useEffect(() => {
        const lastId = localStorage.getItem('lastInfantId')
        if (lastId) {
            setInfantId(lastId)
            fetch(`http://127.0.0.1:8000/api/pain/history/${lastId}?limit=1`)
                .then(res => res.ok ? res.json() : [])
                .then(data => {
                    if (Array.isArray(data) && data.length > 0) {
                        setLatestScan(data[0])
                        setOverallConfidence(Math.round(data[0].confidence * 100))
                    }
                })
                .catch(() => {})
        }
    }, [])

    // Simulate real-time streaming confidence scores
    useEffect(() => {
        if (latestScan) return // Keep fixed to patient's real score once loaded
        const interval = setInterval(() => {
            setBars(prevBars => {
                let totalScore = 0
                const newBars = prevBars.map(bar => {
                    const fluctuation = Math.floor(Math.random() * 11) - 5
                    let newH = bar.h + fluctuation
                    if (newH > 98) newH = 98
                    if (newH < 60) newH = 60
                    totalScore += newH
                    return { ...bar, h: newH }
                })
                const newAvg = Math.round(totalScore / newBars.length)
                setOverallConfidence(newAvg)
                return newBars
            })
        }, 1500)
        return () => clearInterval(interval)
    }, [latestScan])

    return (
        <div className="bg-[#f1f5f9] rounded-2xl p-5 shadow-xl border border-gray-200 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 w-full">
            <div className="flex items-start justify-between mb-4">
                <div>
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
                        {latestScan ? `Confidence Score (${infantId})` : 'Confidence Score'}
                    </p>
                    <div className="flex items-baseline gap-1 mt-1">
                        <span className="text-3xl font-black text-[#1c2b4a]">{overallConfidence}</span>
                        <span className="text-2xl font-bold text-[#1c2b4a]/70">%</span>
                    </div>
                    <p className="text-xs text-indigo-500 font-medium mt-1">
                        {latestScan ? `Verified by AI: ${latestScan.pain_level}` : (overallConfidence > 80 ? 'High Confidence Analysis' : 'Active Facial Monitoring')}
                    </p>
                </div>
                <button className="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center hover:bg-gray-200 transition-colors">
                    <svg viewBox="0 0 24 24" className="w-4 h-4 fill-none stroke-gray-400 stroke-2">
                        <circle cx="5" cy="12" r="1" /><circle cx="12" cy="12" r="1" /><circle cx="19" cy="12" r="1" />
                    </svg>
                </button>
            </div>

            {/* Vertical bar chart */}
            <div className="flex items-end gap-1.5 h-16">
                {bars.map((bar, i) => (
                    <div
                        key={i}
                        className="flex-1 rounded-t-sm transition-all duration-700 ease-in-out"
                        style={{
                            height: `${bar.h}%`,
                            backgroundColor: bar.color,
                            transformOrigin: 'bottom',
                        }}
                    />
                ))}
            </div>

            {/* Labels */}
            <div className="flex justify-between mt-2">
                {bars.map((bar, i) => (
                    <span key={i} className="text-[9px] text-gray-400 font-bold flex-1 text-center">
                        {bar.id}
                    </span>
                ))}
            </div>
        </div>
    )
}
