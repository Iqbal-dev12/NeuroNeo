import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import BackgroundBlobs from '../components/BackgroundBlobs';

const Alerts = () => {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { user } = useAuth();
    const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

    useEffect(() => {
        fetchAlerts();
    }, []);

    const fetchAlerts = async () => {
        if (!user) return;
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${API_URL}/api/pain/alerts`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (!res.ok) throw new Error('Failed to fetch alerts.');
            const data = await res.json();
            setAlerts(data);
        } catch (err) {
            setError(err.message || String(err));
        } finally {
            setLoading(false);
        }
    };

    const updateAlertStatus = async (alertId, newStatus) => {
        try {
            const token = localStorage.getItem('token');
            const res = await fetch(`${API_URL}/api/pain/alerts/${alertId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ alert_status: newStatus })
            });
            
            if (!res.ok) {
                let errorMessage = 'Failed to update alert status';
                try {
                    const errorData = await res.json();
                    if (errorData.detail) errorMessage = Array.isArray(errorData.detail) ? errorData.detail.map(e => e.msg).join(', ') : errorData.detail;
                } catch(e) {}
                throw new Error(errorMessage);
            }
            
            // Re-fetch alerts after successful update
            fetchAlerts();
        } catch (err) {
            alert(`Error: ${err.message}`);
        }
    };

    const formatDate = (dateStr) => {
        if (!dateStr) return 'N/A';
        try {
            const date = new Date(dateStr);
            if (isNaN(date.getTime())) return 'Invalid Date';
            return date.toLocaleString();
        } catch (e) {
            return 'Invalid Date';
        }
    };

    const getStatusColor = (status) => {
        switch(status) {
            case 'active': return 'bg-red-100 text-red-800 border-red-200';
            case 'acknowledged': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
            case 'resolved': return 'bg-green-100 text-green-800 border-green-200';
            default: return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    };

    return (
        <div className="relative min-h-screen bg-[#e0f7ff] font-sans pb-12">
            <BackgroundBlobs />
            <div className="relative z-10 flex flex-col min-h-screen">
                <Navbar />
                <div className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 mt-32">
                    <div className="bg-white rounded-3xl p-8 shadow-xl shadow-blue-900/5 border border-white/50 backdrop-blur-sm animate-fade-in relative overflow-hidden">
                        
                        {/* Decorative Background for Card */}
                        <div className="absolute top-0 right-0 w-64 h-64 bg-red-50 rounded-full blur-3xl opacity-50 -mr-32 -mt-32"></div>

                        <div className="relative z-10">
                            <h2 className="text-3xl font-black text-[#1c2b4a] tracking-tight mb-2">Critical Alerts</h2>
                            <p className="text-gray-500 font-medium mb-8">Manage and respond to severe pain detections across all monitoring sessions.</p>

                            {!user ? (
                                <div className="p-8 text-center border-2 border-dashed border-gray-200 rounded-2xl bg-gray-50">
                                    <h3 className="text-xl font-bold text-[#1c2b4a]">Authentication Required</h3>
                                    <p className="text-gray-500 mt-2">Please log in to view and manage alerts.</p>
                                </div>
                            ) : loading ? (
                                <div className="flex justify-center items-center h-64">
                                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                                </div>
                            ) : error ? (
                                <div className="p-6 bg-red-50 border border-red-100 rounded-2xl flex items-center justify-center gap-3 animate-fade-in">
                                    <span className="text-red-500 bg-white p-2 rounded-full shadow-sm">
                                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                    </span>
                                    <div>
                                        <h3 className="font-bold text-red-800 leading-tight">Connection Issue</h3>
                                        <p className="text-red-600 text-sm mt-0.5">{error}</p>
                                    </div>
                                </div>
                            ) : alerts.length === 0 ? (
                                <div className="p-12 text-center border-2 border-dashed border-gray-200 rounded-2xl bg-gray-50">
                                    <p className="text-gray-500 font-medium text-lg">No alerts found.</p>
                                    <p className="text-gray-400 mt-1">Systems are currently operating normally.</p>
                                </div>
                            ) : (
                                <div className="space-y-4">
                                    {alerts.map((alert) => (
                                        <div key={alert.id} className="bg-white border rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col md:flex-row md:items-center justify-between gap-6">
                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 w-full">
                                                <div>
                                                    <span className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Time</span>
                                                    <span className="text-sm font-semibold text-[#1c2b4a]">{formatDate(alert.created_at)}</span>
                                                </div>
                                                <div>
                                                    <span className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Patient ID</span>
                                                    <span className="text-sm font-semibold text-[#1c2b4a]">{alert.infant_id}</span>
                                                </div>
                                                <div>
                                                    <span className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Severity</span>
                                                    <div className="flex items-center gap-2">
                                                        <span className="relative flex h-3 w-3">
                                                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                                                            <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                                                        </span>
                                                        <span className="text-sm font-bold text-red-600">{alert.pain_level}</span>
                                                    </div>
                                                </div>
                                                <div>
                                                    <span className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Status</span>
                                                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border ${getStatusColor(alert.alert_status)}`}>
                                                        {alert.alert_status.toUpperCase()}
                                                    </span>
                                                </div>
                                            </div>
                                            
                                            <div className="flex gap-3 md:w-auto shrink-0 border-t md:border-t-0 pt-4 md:pt-0">
                                                {alert.alert_status === 'active' && (
                                                    <button 
                                                        onClick={() => updateAlertStatus(alert.id, 'acknowledged')}
                                                        className="px-4 py-2 bg-yellow-50 text-yellow-700 hover:bg-yellow-100 border border-yellow-200 rounded-xl font-bold text-sm transition-colors"
                                                    >
                                                        Acknowledge
                                                    </button>
                                                )}
                                                {['active', 'acknowledged'].includes(alert.alert_status) && (
                                                    <button 
                                                        onClick={() => updateAlertStatus(alert.id, 'resolved')}
                                                        className="px-4 py-2 bg-green-50 text-green-700 hover:bg-green-100 border border-green-200 rounded-xl font-bold text-sm transition-colors"
                                                    >
                                                        Resolve
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Alerts;
