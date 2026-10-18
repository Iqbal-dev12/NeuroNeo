import { Link } from 'react-router-dom'

export default function AboutSection() {
    return (
        <div className="relative rounded-[2rem] overflow-hidden h-full flex flex-col p-10 md:p-12 shadow-2xl border border-indigo-900/20" style={{ background: '#243b6b' }}>
            {/* Dotted grid overlay */}
            <div className="absolute inset-0 dotted-grid opacity-5 pointer-events-none" />

            <div className="relative z-10 flex flex-col h-full">
                {/* Badge */}
                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-white/10 bg-white/5 mb-8 w-fit">
                    <span className="text-white/40 text-[10px] font-bold uppercase tracking-[0.2em]">Impact</span>
                </div>

                <h2 className="text-xl md:text-2xl font-semibold text-white/90 leading-[1.6] mb-8 tracking-wide">
                    Our project focuses on assisting healthcare professionals in detecting neonatal pain using AI-based facial expression analysis. Since infants cannot verbally communicate their pain, this deep learning system provides real-time monitoring support for NICU environments, tracking facial cues to identify discomfort and aid in early medical intervention.
                </h2>

                <div className="mt-auto">
                    <Link
                        to="/learn-more"
                        className="group inline-flex items-center gap-2 text-white/50 font-bold text-sm hover:text-white transition-colors duration-300 border-b border-white/10 pb-1"
                    >
                        Learn More
                    </Link>
                </div>
            </div>
        </div>
    )
}
