"use client"

import { useState } from "react"
import Image from "next/image"
import { motion, AnimatePresence } from "framer-motion"
import { RegionPanel } from "@/components/region-panel"

// Define regions with their data
const regions = [
  {
    id: "northAmerica",
    name: "North America",
    coords: { x: "25%", y: "30%" },
    greenCoverage: 36.2,
    verifiedArea: "1.8B",
    validators: 682,
    lastVerification: "2h ago",
  },
  {
    id: "southAmerica",
    name: "South America",
    coords: { x: "30%", y: "60%" },
    greenCoverage: 48.7,
    verifiedArea: "2.4B",
    validators: 421,
    lastVerification: "4h ago",
  },
  {
    id: "europe",
    name: "Europe",
    coords: { x: "48%", y: "28%" },
    greenCoverage: 34.1,
    verifiedArea: "0.9B",
    validators: 573,
    lastVerification: "1h ago",
  },
  {
    id: "africa",
    name: "Africa",
    coords: { x: "48%", y: "50%" },
    greenCoverage: 29.8,
    verifiedArea: "1.7B",
    validators: 312,
    lastVerification: "6h ago",
  },
  {
    id: "asia",
    name: "Asia",
    coords: { x: "68%", y: "35%" },
    greenCoverage: 31.5,
    verifiedArea: "3.2B",
    validators: 493,
    lastVerification: "3h ago",
  },
  {
    id: "oceania",
    name: "Oceania",
    coords: { x: "80%", y: "65%" },
    greenCoverage: 42.3,
    verifiedArea: "0.6B",
    validators: 201,
    lastVerification: "5h ago",
  },
]

export function Earth() {
  const [activeRegion, setActiveRegion] = useState<string | null>(null)

  const handleRegionHover = (regionId: string) => {
    setActiveRegion(regionId)
  }

  const handleRegionLeave = () => {
    setActiveRegion(null)
  }

  const activeRegionData = regions.find((region) => region.id === activeRegion)

  return (
    <div className="w-full">
      {/* Main container with map and side panel */}
      <div className="flex items-start justify-center gap-8">
        {/* Earth container */}
        <div className="relative w-full max-w-3xl aspect-[4/3] md:aspect-[2/1]">
          {/* Earth base image */}
          <div className="relative w-full h-full">
            <Image src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Equirectangular_projection_SW.jpg/1200px-Equirectangular_projection_SW.jpg" alt="World Map" fill className="object-contain rounded-lg" priority />

            {/* Holographic overlay */}
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 to-green-500/10 rounded-lg mix-blend-overlay" />

            {/* Grid overlay */}
            <div
              className="absolute inset-0 opacity-20 rounded-lg"
              style={{
                backgroundImage:
                  "linear-gradient(rgba(0, 255, 255, 0.2) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 255, 255, 0.2) 1px, transparent 1px)",
                backgroundSize: "30px 30px",
              }}
            />

            {/* Glowing border */}
            <div className="absolute inset-0 rounded-lg border-2 border-cyan-500/40 shadow-[0_0_20px_rgba(0,255,255,0.4)]" />

            {/* Verification nodes - bigger and more reactive */}
            {regions.map((region) => (
              <div
                key={region.id}
                className="absolute cursor-pointer group"
                style={{
                  left: region.coords.x,
                  top: region.coords.y,
                  transform: "translate(-50%, -50%)",
                }}
                onMouseEnter={() => handleRegionHover(region.id)}
                onMouseLeave={handleRegionLeave}
              >
                <div className="relative">
                  {/* Outer pulse ring */}
                  <div className="absolute inset-0 w-8 h-8 rounded-full bg-cyan-400/30 animate-ping group-hover:bg-cyan-300/50" />

                  {/* Middle ring */}
                  <div className="absolute inset-1 w-6 h-6 rounded-full bg-cyan-400/50 animate-pulse group-hover:bg-cyan-300/70" />

                  {/* Inner core */}
                  <div className="relative w-8 h-8 rounded-full bg-cyan-400 group-hover:bg-cyan-300 group-hover:scale-125 transition-all duration-200 shadow-[0_0_15px_rgba(0,255,255,0.6)]" />

                  {/* Center dot */}
                  <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-white" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Side panel - positioned next to the map */}
        <div className="w-80 h-96">
          <AnimatePresence mode="wait">
            {activeRegion && activeRegionData && (
              <motion.div
                key={activeRegion}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.2 }}
                className="w-full h-full"
              >
                <RegionPanel region={activeRegionData} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
