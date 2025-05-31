"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Wallet } from "lucide-react"

export function Header() {
  const [isConnected, setIsConnected] = useState(false)

  const handleConnect = () => {
    setIsConnected(true)
  }

  return (
    <header className="border-b border-cyan-900/30 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="size-8 rounded-full bg-gradient-to-r from-cyan-500 to-green-500 flex items-center justify-center">
            <div className="size-6 rounded-full bg-[#050510] flex items-center justify-center">
              <div className="size-4 rounded-full bg-gradient-to-r from-cyan-400 to-green-400" />
            </div>
          </div>
          <span className="font-bold text-xl tracking-wider bg-gradient-to-r from-cyan-400 to-green-400 bg-clip-text text-transparent">
            VeriGreen
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-8">
          <Link href="#" className="text-gray-400 hover:text-cyan-400 tracking-wide text-sm">
            PROTOCOL
          </Link>
          <Link href="#" className="text-gray-400 hover:text-cyan-400 tracking-wide text-sm">
            LAND OWNER
          </Link>
          <Link href="#" className="text-gray-400 hover:text-cyan-400 tracking-wide text-sm">
            ECOSYSTEM
          </Link>
          <Link href="#" className="text-gray-400 hover:text-cyan-400 tracking-wide text-sm">
            DOCS
          </Link>
        </nav>

        <Button
          onClick={handleConnect}
          variant="outline"
          className={`
            border border-cyan-500/50 text-sm tracking-wider
            ${isConnected ? "bg-cyan-900/20 text-cyan-400" : "bg-transparent text-cyan-400 hover:bg-cyan-900/20"}
          `}
        >
          <Wallet className="mr-2 size-4" />
          {isConnected ? "0x71...3F4a" : "CONNECT WALLET"}
        </Button>
      </div>
    </header>
  )
}
