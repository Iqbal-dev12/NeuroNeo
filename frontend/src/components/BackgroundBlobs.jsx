import React from 'react'

export default function BackgroundBlobs() {
    return (
        <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
            {/* Top right blob */}
            <div className="absolute top-[-10%] right-[-5%] w-[40rem] h-[40rem] bg-indigo-200/40 rounded-full blur-[80px] animate-blob" />
            
            {/* Mid left blob */}
            <div className="absolute top-[30%] left-[-10%] w-[35rem] h-[35rem] bg-sky-200/30 rounded-full blur-[100px] animate-blob animation-delay-2000" />
            
            {/* Bottom right blob */}
            <div className="absolute bottom-[-10%] right-[10%] w-[45rem] h-[45rem] bg-blue-100/40 rounded-full blur-[120px] animate-blob animation-delay-4000" />
            
            {/* Extra subtle center blob */}
            <div className="absolute top-[50%] left-[50%] -translate-x-1/2 -translate-y-1/2 w-[50rem] h-[50rem] bg-white/20 rounded-full blur-[150px]" />
        </div>
    )
}
