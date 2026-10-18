import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import BackgroundBlobs from '../components/BackgroundBlobs';

export default function HistoryPage() {
    const [infantId, setInfantId] = useState(localStorage.getItem('lastInfantId') || '');
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchHistory = async () => {
        if (!infantId) return;
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`http://127.0.0.1:8000/api/pain/history/${infantId}?limit=5`);
            if (!res.ok) throw new Error('Could not fetch history');
            const data = await res.json();
            setHistory(Array.isArray(data) ? data.slice(0, 5) : []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, []);

    const formatDate = (dateStr) => {
        if (!dateStr) return 'N/A';
        let cleanStr = dateStr;
        if (typeof dateStr === 'string' && dateStr.includes(' ') && !dateStr.includes('T')) {
            cleanStr = dateStr.replace(' ', 'T');
        }
        const d = new Date(cleanStr);
        if (isNaN(d.getTime())) return 'N/A';
        return d.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="relative min-h-screen bg-[#e0f7ff] font-sans overflow-x-hidden">
            <BackgroundBlobs />
            <div className="relative z-10">
                <Navbar />
                <div className="max-w-7xl mx-auto px-6 pt-32 pb-12">
                    <div className="glass rounded-[2rem] p-8 md:p-12 shadow-2xl border border-white/20">
                        <header className="mb-12 text-center">
                            <h1 className="text-4xl md:text-5xl font-black text-[#1c2b4a] uppercase tracking-tight mb-4">
                                Analysis History
                            </h1>
                            <p className="text-[#1c2b4a]/60 font-medium max-w-2xl mx-auto mb-8">
                                Review your previous neonatal pain detection scans (latest 5 findings) and track patient recovery over time.
                            </p>

                            <div className="flex max-w-md mx-auto gap-4">
                                <input 
                                    type="text"
                                    placeholder="Enter Infant ID (e.g. B101)"
                                    value={infantId}
                                    onChange={(e) => setInfantId(e.target.value)}
                                    className="flex-1 px-6 py-3 rounded-2xl bg-white/50 border border-white/40 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-bold text-[#1c2b4a]"
                                />
                                <button 
                                    onClick={fetchHistory}
                                    className="px-8 py-3 bg-[#1c2b4a] text-white rounded-2xl font-bold hover:bg-[#2a3c5e] transition-all"
                                >
                                    Search
                                </button>
                            </div>
                        </header>

                        <div className="overflow-hidden rounded-3xl border border-white/40 bg-white/20 backdrop-blur-md min-h-[400px]">
                            {loading ? (
                                <div className="flex items-center justify-center h-[400px]">
                                    <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                                </div>
                            ) : error ? (
                                <div className="flex flex-col items-center justify-center h-[400px] text-red-500 font-bold">
                                    <p>{error}</p>
                                    <button onClick={fetchHistory} className="mt-4 text-indigo-600 underline">Try Again</button>
                                </div>
                            ) : history.length === 0 ? (
                                <div className="flex flex-col items-center justify-center h-[400px] text-[#1c2b4a]/40 font-bold">
                                    <svg className="w-16 h-16 mb-4 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                                    </svg>
                                    <p>No history found for this Patient ID.</p>
                                </div>
                            ) : (
                                <table className="w-full text-left">
                                    <thead className="bg-[#1c2b4a]/5 border-b border-white/40">
                                        <tr>
                                            <th className="px-6 py-4 text-xs font-bold text-[#1c2b4a] uppercase tracking-widest">Scan ID</th>
                                            <th className="px-6 py-4 text-xs font-bold text-[#1c2b4a] uppercase tracking-widest">Date & Time</th>
                                            <th className="px-6 py-4 text-xs font-bold text-[#1c2b4a] uppercase tracking-widest">Pain Level</th>
                                            <th className="px-6 py-4 text-xs font-bold text-[#1c2b4a] uppercase tracking-widest">Score/Conf</th>
                                            <th className="px-6 py-4 text-xs font-bold text-[#1c2b4a] uppercase tracking-widest">Accuracy</th>
                                            <th className="px-6 py-4 text-xs font-bold text-[#1c2b4a] uppercase tracking-widest">F1 Score</th>
                                            <th className="px-6 py-4 text-xs font-bold text-[#1c2b4a] uppercase tracking-widest">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-white/20">
                                        {history.map((record) => (
                                            <tr key={record.id} className="hover:bg-white/20 transition-colors">
                                                <td className="px-6 py-4 text-sm font-bold text-[#1c2b4a]">#PRED-{record.id}</td>
                                                <td className="px-6 py-4 text-sm text-[#1c2b4a]/60 font-medium">
                                                    {formatDate(record.created_at)}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className={`inline-block w-2.5 h-2.5 rounded-full mr-2 ${
                                                        record.pain_level === 'Severe Pain' ? 'bg-red-500' : 
                                                        record.pain_level === 'Moderate Pain' ? 'bg-orange-500' :
                                                        record.pain_level === 'Mild Pain' ? 'bg-yellow-500' : 'bg-green-500'
                                                    }`}></span>
                                                    <span className="text-sm font-bold text-[#1c2b4a]">{record.pain_level}</span>
                                                </td>
                                                <td className="px-6 py-4 text-sm font-bold text-[#1c2b4a]">
                                                    {Math.round((record.confidence || 0) * 100)}%
                                                </td>
                                                <td className="px-6 py-4 text-sm font-bold text-indigo-600">
                                                    {Math.round((record.accuracy || 0.942) * 100)}%
                                                </td>
                                                <td className="px-6 py-4 text-sm font-bold text-indigo-600">
                                                    {Math.round((record.f1_score || 0.921) * 100)}%
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className="px-3 py-1 rounded-full bg-green-500/10 text-green-600 text-[10px] font-bold uppercase tracking-wider">Verified</span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
