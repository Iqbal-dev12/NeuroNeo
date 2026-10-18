import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import BackgroundBlobs from '../components/BackgroundBlobs';

const Login = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        try {
            await login(email, password);
            navigate('/');
        } catch (err) {
            setError(err.message || String(err));
        }
    };

    return (
        <div className="relative min-h-screen bg-[#e0f7ff] font-sans overflow-x-hidden flex flex-col">
            <BackgroundBlobs />
            <div className="relative z-10 flex flex-col min-h-screen">
                <Navbar />

                {/* Main Content */}
                <div className="flex-1 flex items-center justify-center px-6 pt-32 pb-20">
                    <div className="w-full max-w-md animate-slide-up">
                        <div className="bg-white p-8 md:p-10 rounded-[2rem] shadow-2xl shadow-blue-900/10 border border-blue-50 relative overflow-hidden">
                            {/* Decorative blur */}
                            <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50 rounded-full -mr-16 -mt-16 blur-2xl opacity-60"></div>
                            
                            <div className="relative z-10">
                                <div className="text-center mb-8">
                                    <h2 className="text-3xl font-black text-[#1c2b4a] tracking-tight mb-2">
                                        Neonatal Access
                                    </h2>
                                    <p className="text-[#1c2b4a]/60 font-medium text-sm">
                                        Facial Expression Recognition Portal
                                    </p>
                                </div>

                                {error && (
                                    <div className="mb-6 p-4 bg-red-50 border border-red-100 rounded-xl text-red-600 text-sm font-semibold text-center animate-fade-in flex items-center justify-center gap-2">
                                        <svg viewBox="0 0 24 24" className="w-5 h-5 fill-none stroke-current stroke-2">
                                            <circle cx="12" cy="12" r="10"/><path d="M12 8v4m0 4h.01"/>
                                        </svg>
                                        {error}
                                    </div>
                                )}

                                <form onSubmit={handleSubmit} className="flex flex-col gap-5">
                                    <div>
                                        <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Medical Email</label>
                                        <input
                                            type="email"
                                            placeholder="doctor@neonatal.care"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            required
                                            className="w-full bg-[#f8fbff] border border-blue-100 text-[#1c2b4a] rounded-xl px-4 py-3 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-all font-medium"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Password</label>
                                        <input
                                            type="password"
                                            placeholder="••••••••"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            required
                                            className="w-full bg-[#f8fbff] border border-blue-100 text-[#1c2b4a] rounded-xl px-4 py-3 outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-all font-medium"
                                        />
                                    </div>
                                    
                                    <button 
                                        type="submit" 
                                        className="w-full mt-4 shimmer-container shimmer-overlay px-6 py-3.5 bg-indigo-600 text-white rounded-xl font-bold shadow-lg shadow-indigo-900/20 hover:bg-indigo-500 hover:-translate-y-0.5 transition-all outline-none"
                                    >
                                        Sign In
                                    </button>
                                </form>

                                <div className="mt-8 pt-6 border-t border-gray-100 text-center">
                                    <p className="text-sm font-medium text-gray-500">
                                        Don't have an account?{' '}
                                        <Link to="/signup" className="text-indigo-600 font-bold hover:text-indigo-500 transition-colors">
                                            Register
                                        </Link>
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
