import React, { useRef } from 'react'
import { useNavigate } from 'react-router-dom'

// Floating label with connector dot
function FloatingLabel({ text, className, dotColor = '#ff4d4f', delay = '0s' }) {
    return (
        <div
            className={`animate-float-label absolute flex items-center gap-2 glass rounded-full px-3 py-1.5 shadow-lg ${className}`}
            style={{ animationDelay: delay }}
        >
            <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: dotColor }}></span>
            <span className="text-xs font-semibold text-[#1c2b4a] whitespace-nowrap">{text}</span>
        </div>
    )
}

// SVG Anatomical Heart removed

export default function HeroSection() {
    const navigate = useNavigate()
    const fileInputRef = useRef(null)

    const handleFileChange = (e) => {
        const file = e.target.files[0]
        if (!file) return
        navigate('/analyze', { state: { file } })
        // Reset so the same file can be re-selected if needed
        e.target.value = ''
    }

    return (
        <section className="min-h-screen flex items-center pt-32 pb-8 overflow-hidden">
            {/* Hidden file input — accepts images AND videos */}
            <input
                ref={fileInputRef}
                type="file"
                accept="image/*,video/*"
                className="hidden"
                onChange={handleFileChange}
            />

            <div className="max-w-7xl mx-auto px-6 w-full">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
                    
                    {/* LEFT: Medical Heart Illustration */}
                    <div className="relative flex items-center justify-center animate-slide-left order-2 lg:order-1 lg:translate-x-12" style={{ animationDelay: '0.2s' }}>
                        {/* Glow backdrop */}
                        <div className="absolute inset-0 rounded-full opacity-60 flex items-center justify-center pointer-events-none">
                            <div className="w-[500px] h-[500px] bg-sky-100/30 blur-[100px] rounded-full animate-glow-pulse" />
                        </div>

                        {/* Heart Image */}
                        <div className="relative w-80 h-80 md:w-96 md:h-96 lg:w-[540px] lg:h-[540px] z-10 transition-transform duration-700 hover:scale-105">
                            <img
                                src="/photo.jpeg"
                                alt="Neonatal Pain Detection Visualization"
                                className="w-full h-full object-contain rounded-3xl"
                            />
                        </div>
                    </div>

                    {/* RIGHT: Heading + CTA */}
                    <div className="flex flex-col gap-6 animate-slide-right pb-10 order-1 lg:order-2" style={{ animationDelay: '0.4s' }}>
                        <div>
                            <h1 className="text-[3rem] md:text-5xl xl:text-[4.5rem] font-bold text-[#1c2b4a] leading-[1.1] tracking-tight mb-2 uppercase">
                                AI-BASED NEONATAL
                                <br />
                                PAIN DETECTION
                            </h1>
                        </div>

                        <p className="text-[#1c2b4a]/60 text-sm md:text-base leading-relaxed max-w-md font-medium">
                            A deep learning system that analyzes neonatal facial expressions to detect pain levels in infants and assist healthcare professionals in early diagnosis.
                        </p>

                        <div className="flex flex-col sm:flex-row flex-wrap items-center gap-4 mt-4">
                            <button 
                                onClick={() => fileInputRef.current?.click()}
                                className="w-full sm:w-auto text-center px-6 py-3 bg-[#1c2b4a] text-white rounded-full font-bold shadow-lg shadow-indigo-200 hover:bg-[#2a3c5e] hover:-translate-y-0.5 transition-all text-sm flex items-center justify-center gap-2"
                            >
                                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                                </svg>
                                Upload Infant Image / Video
                            </button>
                            <button 
                                onClick={() => navigate('/analyze', { state: { demoSample: 'S001_Pain_1_[0]_20s.mp4' } })}
                                className="w-full sm:w-auto text-center px-6 py-3 bg-white/90 border border-indigo-200 text-[#1c2b4a] rounded-full font-bold shadow-sm hover:bg-white hover:-translate-y-0.5 transition-all text-sm flex items-center justify-center gap-2"
                            >
                                <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span>
                                Try Demo Samples (Direct)
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    )
}
