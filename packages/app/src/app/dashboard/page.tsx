'use client'

import React, { useState } from 'react'
import { useAccount } from 'wagmi'
import { Connect } from '@/components/Connect'
import { useRouter } from 'next/navigation'
import forestImg from '@/assets/icons/forest.png'
import { TileSidebar, TileData } from '@/components/TileSidebar'

// Mock tile data

const GRID_ROWS = 4
const GRID_COLS = 8
const TILE_SIZE = 96 // px
const GAP_SIZE = 2 // px (thin line)

const TILES: TileData[] = Array.from({ length: GRID_ROWS * GRID_COLS }, (_, i) => {
  const row = Math.floor(i / GRID_COLS)
  const col = i % GRID_COLS
  return {
    id: i + 1,
    row: row,
    col: col,
    alerts: Math.random() > 0.8 ? Math.floor(Math.random() * 3) + 1 : 0, // Mock alerts
    tokensEarned: Math.floor(Math.random() * 500) + 500,
    coordinates: { lat: -36.1608 + i * 0.01, lng: -61.2211 + i * 0.01 },
    metrics: {
      airQuality: Math.floor(Math.random() * 50) + 50,
      forestCoverage: Math.floor(Math.random() * 30) + 60,
      ndviScore: Math.floor(Math.random() * 20) + 70,
      carbonEmissions: Math.floor(Math.random() * 100000) + 300000,
      temperature: Math.floor(Math.random() * 5) + 5,
      biodiversityIndex: Math.floor(Math.random() * 20) + 70,
    },
    trends: {
      airQualityTrend: Math.random() > 0.6 ? (Math.random() > 0.5 ? 'up' : 'down') : 'stable',
      forestTrend: Math.random() > 0.6 ? (Math.random() > 0.5 ? 'up' : 'down') : 'stable',
      emissionsTrend: Math.random() > 0.6 ? (Math.random() > 0.5 ? 'up' : 'down') : 'stable',
    },
    lastUpdated: new Date(Date.now() - Math.random() * 86400000 * 7).toISOString(), // Mock last updated within a week
  }
})

// Get the static path for the forest image
const forestImgUrl = forestImg.src || forestImg

export default function DashboardPage() {
  const { isConnected } = useAccount()
  const router = useRouter()
  const [selectedTile, setSelectedTile] = useState<TileData | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  React.useEffect(() => {
    if (!isConnected) {
      router.push('/')
    }
  }, [isConnected, router])

  // Calculate the full grid size (excluding gaps)
  const gridWidth = TILE_SIZE * GRID_COLS + GAP_SIZE * (GRID_COLS - 1)
  const gridHeight = TILE_SIZE * GRID_ROWS + GAP_SIZE * (GRID_ROWS - 1)

  if (!isConnected) {
    return (
      <div className='flex flex-col items-center justify-center min-h-screen p-4'>
        <h1 className='text-2xl font-bold mb-4'>Please Connect Your Wallet</h1>
        <Connect />
      </div>
    )
  }

  return (
    <div className='min-h-screen bg-black flex flex-col items-center justify-start py-8'>
      <h1 className='text-4xl font-bold text-white mb-2'>Your Land Portfolio</h1>
      <p className='text-lg text-gray-300 mb-8 text-center max-w-2xl'>
        Monitor environmental metrics and earn tokens from your sustainable land management practices.
      </p>
      <div className='relative rounded-2xl overflow-hidden shadow-2xl bg-gray-200 p-4'>
        <div
          className='relative z-10 grid bg-white'
          style={{
            gridTemplateColumns: `repeat(${GRID_COLS}, minmax(${TILE_SIZE}px, 1fr))`,
            gridTemplateRows: `repeat(${GRID_ROWS}, minmax(${TILE_SIZE}px, 1fr))`,
            gap: `${GAP_SIZE}px`,
            width: gridWidth,
            height: gridHeight,
          }}>
          {TILES.map((tile, idx) => {
            const row = Math.floor(idx / GRID_COLS)
            const col = idx % GRID_COLS
            const bgPosX = -col * (TILE_SIZE + GAP_SIZE) + 'px'
            const bgPosY = -row * (TILE_SIZE + GAP_SIZE) + 'px'
            return (
              <button
                key={tile.id}
                className='group rounded-lg flex items-center justify-center text-white font-bold text-xs shadow-lg transition-all relative overflow-hidden focus:z-20 aspect-square'
                onClick={() => {
                  setSelectedTile(tile)
                  setSidebarOpen(true)
                }}
                style={{
                  width: TILE_SIZE,
                  minWidth: TILE_SIZE,
                  minHeight: TILE_SIZE,
                  backgroundImage: `url(${forestImgUrl})`,
                  backgroundSize: `${gridWidth}px ${gridHeight}px`,
                  backgroundPosition: `${bgPosX} ${bgPosY}`,
                  backgroundRepeat: 'no-repeat',
                }}>
                <span className='absolute inset-0 bg-black/30 opacity-60 group-hover:opacity-0 group-hover:bg-black/0 transition-all duration-200' />
                <span className='absolute inset-0 pointer-events-none group-hover:ring-4 group-hover:ring-green-400 group-hover:shadow-2xl group-hover:scale-105 transition-all duration-200 rounded-lg' />
                <span className='absolute top-1 left-1 bg-black/70 rounded px-1 text-xs z-10'>{tile.id}</span>
              </button>
            )
          })}
        </div>
        <div className='text-center text-gray-500 text-xs mt-4'>Click any parcel to view detailed information</div>
      </div>
      <TileSidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} tileData={selectedTile} />
    </div>
  )
}
