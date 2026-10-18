import React, { useEffect } from 'react'
import { Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import BackgroundBlobs from '../components/BackgroundBlobs'

export default function LearnMore() {
    // Scroll to top on mount
    useEffect(() => {
        window.scrollTo(0, 0)
    }, [])

    return (
        <div className="relative min-h-screen bg-[#e0f7ff] font-sans overflow-x-hidden">
            <BackgroundBlobs />
            <div className="relative z-10">
                <Navbar />

                <div className="pt-32 pb-20 px-6">
                    <div className="max-w-4xl mx-auto">
                        {/* Header */}
                        <div className="mb-16 animate-slide-up">
                            <Link to="/" className="inline-flex items-center gap-2 text-indigo-600 font-bold text-sm mb-6 hover:gap-3 transition-all">
                                <svg viewBox="0 0 24 24" className="w-4 h-4 fill-none stroke-current stroke-2"><path d="M19 12H5M12 19l-7-7 7-7" /></svg>
                                Back to Home
                            </Link>
                            <h1 className="text-4xl md:text-5xl font-black text-[#1c2b4a] tracking-tight mb-4">
                                Platform Overview
                            </h1>
                            <div className="w-20 h-1.5 bg-indigo-600 rounded-full"></div>
                        </div>

                        {/* Section 1 — Overview */}
                        <section className="mb-20 animate-slide-up" style={{ animationDelay: '0.1s' }}>
                            <div className="bg-white p-8 md:p-12 rounded-[2rem] shadow-xl shadow-blue-900/5 border border-blue-50">
                                <h2 className="text-2xl font-bold text-[#1c2b4a] mb-6 flex items-center gap-3">
                                    Overview
                                </h2>
                                <p className="text-lg text-[#1c2b4a]/70 leading-relaxed font-medium">
                                    NeuralMedics provides an intelligent AI-based platform for real-time neonatal pain detection.
                                    The system analyzes infant facial expressions using deep learning models (MobileNetV3) to detect
                                    visual indicators of discomfort, supporting prompt and accurate medical intervention in NICU environments.
                                </p>
                            </div>
                        </section>

                        {/* Section 2 — Key System Features */}
                        <section className="mb-20 animate-slide-up" style={{ animationDelay: '0.2s' }}>
                            <div className="bg-white p-8 md:p-12 rounded-[2.5rem] shadow-2xl shadow-blue-900/5 border border-blue-50 relative overflow-hidden">
                                {/* Decorative blur */}
                                <div className="absolute -top-24 -right-24 w-64 h-64 bg-indigo-50 rounded-full blur-3xl opacity-60"></div>

                                <div className="relative z-10">
                                    <h2 className="text-3xl font-black text-[#1c2b4a] mb-12 flex items-center gap-4">
                                        <div className="w-2 h-10 bg-indigo-600 rounded-full"></div>
                                        Key System Features
                                    </h2>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 lg:gap-8">
                                        {[
                                            { title: 'Infant Face Detection', desc: 'Securely acquires and isolates infant facial regions from live camera feeds.' },
                                            { title: 'Facial Expression Analysis', desc: 'Analyzes micro-expressions and facial cues mathematically using Computer Vision and OpenCV.' },
                                            { title: 'Deep Learning Pain Classification', desc: 'Employs MobileNetV3 to classify pain into No Pain, Pain categories.' },
                                            { title: 'Report Generation', desc: 'Generates a detailed report of the infant pain analysis including predicted pain level, confidence score, and timestamp.' },
                                            { title: 'History', desc: 'Stores previous analysis results so users can view past pain detection records.' },


                                        ].map((feature, i) => (
                                            <div key={i} className="group relative bg-[#f8fbff]/50 backdrop-blur-sm p-8 rounded-[2rem] border border-blue-100 hover:bg-white hover:shadow-2xl hover:shadow-indigo-900/10 hover:-translate-y-2 transition-all duration-500">
                                                <div className="flex flex-col gap-6">
                                                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-indigo-700 text-white flex items-center justify-center font-black text-xl shadow-lg shadow-indigo-200 group-hover:scale-110 group-hover:rotate-6 transition-all duration-500">
                                                        {i + 1}
                                                    </div>
                                                    <div>
                                                        <h4 className="text-[#1c2b4a] font-black text-xl mb-3 leading-tight group-hover:text-indigo-600 transition-colors">{feature.title}</h4>
                                                        <p className="text-[#1c2b4a]/60 text-sm leading-relaxed font-medium">{feature.desc}</p>
                                                    </div>
                                                </div>
                                                {/* Corner Decoration */}
                                                <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-20 transition-opacity duration-500">
                                                    <svg viewBox="0 0 24 24" className="w-8 h-8 fill-current text-indigo-600"><path d="M12 2L4.5 20.29l.71.71L12 18l6.79 3 .71-.71z" /></svg>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </section>

                        {/* Section 3 — How It Works */}
                        <section className="mb-20 animate-slide-up" style={{ animationDelay: '0.3s' }}>
                            <div className="bg-white p-8 md:p-12 rounded-[2rem] shadow-xl shadow-blue-900/5 border border-blue-50">
                                <h2 className="text-2xl font-bold text-[#1c2b4a] mb-10">
                                    How It Works
                                </h2>

                                <div className="bg-[#f8fbff] p-10 md:p-14 rounded-[3rem] border border-blue-100 relative overflow-hidden">
                                    <div className="absolute inset-0 dotted-grid opacity-10 pointer-events-none" />

                                    <div className="relative z-10">
                                        <p className="text-[#1c2b4a]/40 font-bold text-xs uppercase tracking-[0.2em] mb-10 text-center">System Flow Architecture</p>

                                        <div className="flex flex-col items-center gap-4">
                                            {[
                                                'Infant Image / Camera Input',
                                                'Face Detection (OpenCV)',
                                                'Facial Feature Extraction',
                                                'Deep Learning Model (MobileNetV3)',
                                                'Pain Level Prediction'
                                            ].map((step, i, arr) => (
                                                <React.Fragment key={i}>
                                                    <div className="bg-white border border-blue-100 py-4 px-8 rounded-xl text-[#1c2b4a] font-bold text-sm md:text-base w-full max-w-sm text-center shadow-sm">
                                                        {step}
                                                    </div>
                                                    {i < arr.length - 1 && (
                                                        <div className="w-0.5 h-6 bg-gradient-to-b from-indigo-200 to-transparent"></div>
                                                    )}
                                                </React.Fragment>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </section>

                        {/* Section 4 — Real-World Impact */}
                        <section className="animate-slide-up" style={{ animationDelay: '0.4s' }}>
                            <div className="bg-white p-8 md:p-12 rounded-[2rem] shadow-xl shadow-blue-900/5 border border-blue-50 overflow-hidden relative">
                                <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-50 rounded-full -mr-32 -mt-32 blur-3xl opacity-50"></div>

                                <h2 className="text-2xl font-bold text-[#1c2b4a] mb-6 relative z-10">
                                    Real-World Impact
                                </h2>
                                <p className="text-lg text-[#1c2b4a]/70 leading-relaxed font-medium relative z-10">
                                    Since infants cannot verbally communicate their discomfort, recognizing neonatal pain is
                                    a significant challenge. NeuralMedics supports pediatric care by enabling early,
                                    objective detection of pain through AI expression analysis, assisting healthcare professionals
                                    in delivering prompt, accurate interventions.
                                </p>
                            </div>
                        </section>
                    </div>
                </div>

                {/* Simple Footer */}
                <footer className="py-10 border-t border-gray-100 text-center">
                    <p className="text-gray-400 text-sm font-medium">© 2026 NeuralMedics Platform Analysis. Neonatal Care.</p>
                </footer>
            </div>
        </div>
    )
}
