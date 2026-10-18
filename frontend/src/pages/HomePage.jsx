import React from 'react'
import Navbar from '../components/Navbar'
import HeroSection from '../components/HeroSection'
import EcgCard from '../components/EcgCard'
import BloodPressureCard from '../components/BloodPressureCard'
import AboutSection from '../components/AboutSection'
import BackgroundBlobs from '../components/BackgroundBlobs'

export default function HomePage() {
    return (
        <div className="relative min-h-screen bg-[#e0f7ff] font-sans overflow-x-hidden">
            <BackgroundBlobs />
            <div className="relative z-10">
                <Navbar />

            <HeroSection />

            {/* Bottom Grid Section */}
            <section id="solutions" className="pb-20 px-6">
                <div className="max-w-7xl mx-auto">
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                        {/* Cards Column */}
                        <div className="lg:col-span-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-1 gap-6">
                            <EcgCard />
                            <BloodPressureCard />
                        </div>
                        
                        {/* About Column */}
                        <div className="lg:col-span-7">
                            <AboutSection />
                        </div>
                    </div>
                </div>
            </section>

            <footer className="py-8 px-6 text-center">
                <p className="text-[#1c2b4a]/40 text-sm font-bold">
                    © 2026 NeuralMedics. All rights reserved. Advancing Neonatal Care.
                </p>
            </footer>
            </div>
        </div>
    )
}
