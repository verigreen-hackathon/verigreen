"use client"

import { useRef } from "react"
import { motion } from "framer-motion"

const tickerItems = [
  "AMAZON BASIN: 24,532 NEW HECTARES VERIFIED",
  "SATELLITE IMAGERY UPDATED: 2.3TB NEW DATA",
  "REFORESTATION PROGRESS: 103% OF QUARTERLY TARGET",
]

export function Ticker() {
  const tickerRef = useRef<HTMLDivElement>(null)

  return (
    <div className="h-8 bg-black/60 backdrop-blur-md border border-cyan-900/50 rounded-full overflow-hidden shadow-lg">
      <div className="h-full flex items-center">
        <div className="bg-cyan-500 text-black text-xs font-bold px-3 h-full flex items-center rounded-l-full">
          LIVE
        </div>
        <div className="overflow-hidden flex-1 relative h-full">
          <motion.div
            ref={tickerRef}
            className="absolute whitespace-nowrap h-full flex items-center gap-8 px-4"
            animate={{
              x: [0, -3000],
            }}
            transition={{
              x: {
                repeat: Number.POSITIVE_INFINITY,
                repeatType: "loop",
                duration: 30,
                ease: "linear",
              },
            }}
          >
            {[...tickerItems, ...tickerItems].map((item, index) => (
              <span key={index} className="text-xs text-white tracking-wider">
                {item}
              </span>
            ))}
          </motion.div>
        </div>
      </div>
    </div>
  )
}
