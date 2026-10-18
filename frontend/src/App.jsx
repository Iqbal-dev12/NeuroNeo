import React from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import LearnMore from './pages/LearnMore'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Report from './pages/Report'
import History from './pages/History'
import Analyze from './pages/Analyze'
import { AuthProvider } from './context/AuthContext'

export default function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/learn-more" element={<LearnMore />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/signup" element={<Signup />} />
                    <Route path="/report" element={<Report />} />
                    <Route path="/history" element={<History />} />
                    <Route path="/analyze" element={<Analyze />} />
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    )
}
