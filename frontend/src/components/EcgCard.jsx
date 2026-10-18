import React, { useRef, useEffect, useState } from 'react'

// Animated ECG waveform on canvas
export default function EcgCard() {
    const canvasRef = useRef(null)
    const animRef = useRef(null)
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
                    }
                })
                .catch(() => {})
        }
    }, [])

    useEffect(() => {
        const canvas = canvasRef.current
        if (!canvas) return
        const ctx = canvas.getContext('2d')
        const W = canvas.width
        const H = canvas.height
        const midY = H / 2

        // Base facial landmark nodes (normalized)
        const baseNodes = [
            { id: 'leftEye', x: 0.35, y: 0.35 },
            { id: 'rightEye', x: 0.65, y: 0.35 },
            { id: 'nose', x: 0.5, y: 0.6 },
            { id: 'mouthLeftArea', x: 0.38, y: 0.75 },
            { id: 'mouthRightArea', x: 0.62, y: 0.75 },
            { id: 'mouthCenter', x: 0.5, y: 0.8 },
            { id: 'leftCheek', x: 0.25, y: 0.55 },
            { id: 'rightCheek', x: 0.75, y: 0.55 }
        ]

        // Connections between nodes to form a mesh
        const connections = [
            [0, 2], [1, 2], // eyes to nose
            [0, 6], [1, 7], // eyes to cheeks
            [6, 3], [7, 4], // cheeks to mouth corners
            [3, 5], [4, 5], // mouth corners to mouth center
            [2, 3], [2, 4], // nose to mouth corners
        ]

        let time = 0

        function draw() {
            ctx.clearRect(0, 0, W, H)

            // Draw faint scanning grid
            ctx.strokeStyle = 'rgba(245, 158, 11, 0.08)' // Amber matching 'text-[#f59e0b]'
            ctx.lineWidth = 0.5
            // Animate grid panning slightly
            const gridOffset = (time * 10) % 20
            for (let x = -20; x < W; x += 20) {
                ctx.beginPath(); ctx.moveTo(x + gridOffset, 0); ctx.lineTo(x + gridOffset, H); ctx.stroke()
            }
            for (let y = 0; y < H; y += 10) {
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke()
            }

            // Animate nodes with perlin-like slight random movement simulation based on time
            const animatedNodes = baseNodes.map((node, i) => {
                // Unique offset per node based on index
                const offsetX = Math.sin(time * 2 + i) * 0.02
                const offsetY = Math.cos(time * 2.5 + i * 1.5) * 0.02
                return {
                    x: (node.x + offsetX) * W,
                    y: (node.y + offsetY) * H
                }
            })

            // Draw scanning line overlay
            const scanY = (time * 30) % H
            ctx.beginPath()
            ctx.strokeStyle = 'rgba(245, 158, 11, 0.3)'
            ctx.lineWidth = 1.5
            ctx.moveTo(0, scanY)
            ctx.lineTo(W, scanY)
            ctx.stroke()

            // Draw connections mesh
            ctx.beginPath()
            ctx.strokeStyle = 'rgba(233, 230, 20, 0.4)'
            ctx.lineWidth = 1.5
            ctx.lineJoin = 'round'

            connections.forEach(([i, j]) => {
                const n1 = animatedNodes[i]
                const n2 = animatedNodes[j]
                ctx.moveTo(n1.x, n1.y)
                ctx.lineTo(n2.x, n2.y)
            })
            ctx.stroke()

            // Draw pulsing nodes
            animatedNodes.forEach((node, i) => {
                const pulse = Math.sin(time * 4 + i) * 0.5 + 0.5 // 0 to 1
                const radius = 2 + pulse * 2

                ctx.beginPath()
                // Highlight specific nodes occasionally
                const isActive = (Math.floor(time) % baseNodes.length) === i
                if (isActive) {
                    ctx.fillStyle = '#f50b0bff'
                    ctx.shadowColor = '#1fee10ff'
                    ctx.shadowBlur = 6
                } else {
                    ctx.fillStyle = 'rgba(252, 174, 4, 0.6)'
                    ctx.shadowBlur = 0
                }

                ctx.arc(node.x, node.y, radius, 0, Math.PI * 2)
                ctx.fill()
            })

            time += 0.03
            animRef.current = requestAnimationFrame(draw)
        }

        draw()
        return () => cancelAnimationFrame(animRef.current)
    }, [])

    return (
        <div className="bg-[#f1f5f9] rounded-2xl p-5 shadow-xl border border-gray-200 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 w-full">
            <div className="flex items-start justify-between mb-3">
                <div>
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest">
                        {latestScan ? `Latest Scan (${infantId})` : 'Pain Level'}
                    </p>
                    <div className="flex items-baseline gap-1.5 mt-1">
                        <span className={`text-xl font-black ${
                            latestScan?.pain_level?.includes('Severe')
                                ? 'text-red-600'
                                : latestScan?.pain_level?.includes('Moderate')
                                    ? 'text-orange-500'
                                    : latestScan?.pain_level?.includes('Mild')
                                        ? 'text-amber-500'
                                        : 'text-[#1c2b4a]'
                        }`}>
                            {latestScan?.pain_level || 'Moderate Pain'}
                        </span>
                    </div>
                    <div className="flex items-center gap-1.5 mt-2">
                        <span className={`inline-block w-2 h-2 rounded-full animate-pulse ${
                            latestScan?.pain_level?.includes('Severe') ? 'bg-red-500' : 'bg-[#f59e0b]'
                        }`}></span>
                        <span className="text-xs text-[#f59e0b] font-medium">
                            {latestScan ? 'Real-Time Diagnosis' : 'AI Facial Landmark Mesh'}
                        </span>
                    </div>
                </div>
                <button className="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center hover:bg-gray-200 transition-colors">
                    <svg viewBox="0 0 24 24" className="w-4 h-4 fill-none stroke-gray-400 stroke-2">
                        <circle cx="5" cy="12" r="1" /><circle cx="12" cy="12" r="1" /><circle cx="19" cy="12" r="1" />
                    </svg>
                </button>
            </div>
            <canvas ref={canvasRef} width={240} height={60} className="w-full rounded-xl" />
        </div>
    )
}
