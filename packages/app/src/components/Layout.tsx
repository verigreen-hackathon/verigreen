import React, { PropsWithChildren } from 'react'
import { Header } from './Header'
import { Footer } from './Footer'

export function Layout(props: PropsWithChildren) {
  return (
    <div>
      <Header />
      <main className="min-h-screen bg-[#050510] font-mono text-white overflow-hidden">
                
      <div
              className=" inset-0 z-0 opacity-20"
        style={{
          backgroundImage:
            "linear-gradient(#0f0f2f 1px, transparent 1px), linear-gradient(90deg, #0f0f2f 1px, transparent 1px)",
          backgroundSize: "40px 40px",
        }}
      >

      </div>
      {props.children}
      

      <Footer />
    </main>
    </div>
        
  )
}
