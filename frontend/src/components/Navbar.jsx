import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'Report', path: '/report' },
    { name: 'History', path: '/history' }
]

export default function Navbar() {
    const { user, logout } = useAuth()
    const navigate = useNavigate()
    const currentPath = window.location.pathname

    const handleLogout = () => {
        logout()
        navigate('/login')
    }

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 py-4">
            <div className="max-w-7xl mx-auto px-6 h-20 rounded-[2rem] border border-white/10 shadow-2xl shadow-blue-950/20 flex items-center justify-between transition-all duration-300" style={{ background: '#243b6b' }}>
                {/* Logo: Neuralmedics */}
                <div onClick={() => navigate('/')} className="flex items-center gap-2 animate-slide-left cursor-pointer">
                    <div className="w-8 h-8 rounded-lg bg-white/10 backdrop-blur-sm flex items-center justify-center p-1.5 shadow-sm border border-white/10">
                        <svg viewBox="0 0 24 24" className="w-full h-full text-white fill-current">
                            <path d="M12 2L4 5v11c0 5.52 4.48 10 10 10s10-4.48 10-10V5l-8-3zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" />
                        </svg>
                    </div>
                    <span className="text-white font-bold text-xl tracking-tight">NeuralMedics</span>
                </div>

                {/* Navigation Pills */}
                <div className="flex items-center gap-1 bg-white/5 backdrop-blur-md rounded-full p-1 border border-white/10 shadow-sm">
                    {navLinks.map((link) => (
                        <button
                            key={link.name}
                            onClick={() => navigate(link.path)}
                            className={`px-6 py-2 rounded-full text-[13px] font-bold transition-all duration-300 ${currentPath === link.path
                                ? 'bg-white text-[#243b6b] shadow-lg'
                                : 'text-white/60 hover:text-white hover:bg-white/10'
                                }`}
                        >
                            <div className="flex items-center gap-2">
                                {currentPath === link.path && (
                                    <span className="grid grid-cols-2 gap-0.5 opacity-80 scale-90">
                                        <span className="w-1 h-1 rounded-full bg-[#243b6b]/40"></span>
                                        <span className="w-1 h-1 rounded-full bg-[#243b6b]/40"></span>
                                        <span className="w-1 h-1 rounded-full bg-[#243b6b]/40"></span>
                                        <span className="w-1 h-1 rounded-full bg-[#243b6b]/40"></span>
                                    </span>
                                )}
                                {link.name}
                            </div>
                        </button>
                    ))}
                </div>

                {/* Auth Buttons */}
                <div className="animate-slide-right flex items-center gap-4">
                    {user ? (
                        <>
                            <div className="text-white/90 font-bold text-[13px] flex items-center gap-2">
                                <span className="w-6 h-6 rounded-full bg-indigo-500 flex items-center justify-center text-[10px] text-white uppercase shadow-inner">
                                    {user.full_name ? user.full_name.charAt(0) : user.email.charAt(0)}
                                </span>
                                <span className="hidden sm:inline-block truncate max-w-[100px]">
                                    {user.full_name || user.email}
                                </span>
                            </div>
                            <button 
                                onClick={handleLogout}
                                className="text-white/60 font-bold text-[13px] hover:text-[#ff4d4f] transition-colors border-l border-white/20 pl-4"
                            >
                                Logout
                            </button>
                        </>
                    ) : (
                        <>
                            <Link to="/login" className="text-white/80 font-bold text-[13px] hover:text-white transition-colors">
                                Login
                            </Link>
                            <Link to="/signup" className="shimmer-container shimmer-overlay px-6 py-2.5 bg-indigo-600 text-white rounded-full font-bold text-[13px] shadow-lg shadow-indigo-900/20 hover:bg-indigo-500 hover:-translate-y-0.5 transition-all border border-white/10">
                                Sign up
                            </Link>
                        </>
                    )}
                </div>
            </div>
        </nav>
    )
}
