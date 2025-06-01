import { X, TrendingUp, TrendingDown, Minus, AlertTriangle, Coins } from 'lucide-react'
// Assuming TileData is defined elsewhere, if not, define it here or in a separate types file
// Example minimal definition:
export type TileData = {
  id: number
  row: number
  col: number
  alerts: number
  tokensEarned: number
  coordinates: { lat: number; lng: number }
  metrics: {
    airQuality: number // Using airQuality as a placeholder for VeriGreen Score based on the code logic
    forestCoverage: number
    ndviScore: number
    carbonEmissions: number
    temperature: number // Using temperature for Average Temperature
    biodiversityIndex: number
  }
  trends: {
    airQualityTrend: 'up' | 'down' | 'stable' // Placeholder trend for VeriGreen Score
    forestTrend: 'up' | 'down' | 'stable'
    emissionsTrend: 'up' | 'down' | 'stable'
  }
  lastUpdated: string
}

interface TileSidebarProps {
  isOpen: boolean
  onClose: () => void
  tileData: TileData | null
}

export const TileSidebar = ({ isOpen, onClose, tileData }: TileSidebarProps) => {
  if (!tileData) return null

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUp className='w-4 h-4 text-green-400' />
      case 'down':
        return <TrendingDown className='w-4 h-4 text-red-400' />
      case 'stable':
        return <Minus className='w-4 h-4 text-gray-400' />
    }
  }

  const getQualityColor = (value: number) => {
    if (value >= 80) return 'text-green-400'
    if (value >= 60) return 'text-yellow-400'
    if (value >= 40) return 'text-orange-400'
    return 'text-red-400'
  }

  // Calculate tile number based on row and col - assuming 8 columns
  const tileNumber = tileData.row * 8 + tileData.col + 1

  return (
    <>
      {/* Sidebar */}
      <div
        className={`
        fixed top-0 right-0 h-full w-96 bg-black shadow-2xl transform transition-transform duration-300 ease-in-out z-50
        ${isOpen ? 'translate-x-0' : 'translate-x-full'}
      `}>
        <div className='flex flex-col h-full'>
          {/* Header */}
          <div className='flex items-center justify-between p-6 border-b border-gray-700'>
            <div>
              <h3 className='text-xl font-bold text-white'>Tile {tileNumber}</h3>
            </div>
            <button onClick={onClose} className='p-2 hover:bg-gray-800 rounded-lg transition-colors'>
              <X className='w-5 h-5 text-gray-400' />
            </button>
          </div>

          {/* Content */}
          <div className='flex-1 overflow-y-auto p-6'>
            {/* Alerts */}
            {tileData.alerts > 0 && (
              <div className='mb-6 p-4 bg-red-900/30 border border-red-700 rounded-lg'>
                <div className='flex items-center space-x-2'>
                  <AlertTriangle className='w-5 h-5 text-red-400' />
                  <span className='font-medium text-red-300'>
                    {tileData.alerts} Active Alert{tileData.alerts > 1 ? 's' : ''}
                  </span>
                </div>
              </div>
            )}

            {/* Tokens Earned */}
            <div className='mb-6 p-4 bg-gradient-to-r from-yellow-900/30 to-orange-900/30 border border-yellow-700 rounded-lg'>
              <div className='flex items-center space-x-3'>
                <Coins className='w-6 h-6 text-yellow-400' />
                <div>
                  <h4 className='font-medium text-white'>Tokens Earned</h4>
                  <p className='text-2xl font-bold text-yellow-400'>{tileData.tokensEarned.toLocaleString()}</p>
                  <p className='text-sm text-gray-300'>VeriGreen Reward Tokens</p>
                </div>
              </div>
            </div>

            {/* Coordinates */}
            <div className='mb-6 p-4 bg-gray-800 rounded-lg'>
              <h4 className='font-medium text-white mb-2'>Location</h4>
              <div className='text-sm text-gray-300'>
                <div>Latitude: {tileData.coordinates.lat.toFixed(4)}°</div>
                <div>Longitude: {tileData.coordinates.lng.toFixed(4)}°</div>
              </div>
            </div>

            {/* Metrics */}
            <div className='space-y-6'>
              <h4 className='font-medium text-white'>Environmental Metrics</h4>

              {/* VeriGreen Score */}
              <div className='space-y-2'>
                <div className='flex items-center justify-between'>
                  <span className='text-sm text-gray-300'>VeriGreen Score</span>
                  <div className='flex items-center space-x-2'>
                    {getTrendIcon(tileData.trends.airQualityTrend)}
                    <span className={`font-medium ${getQualityColor(tileData.metrics.airQuality)}`}>
                      {tileData.metrics.airQuality}%
                    </span>
                  </div>
                </div>
                <div className='w-full bg-gray-700 rounded-full h-2'>
                  <div
                    className={`h-2 rounded-full ${
                      tileData.metrics.airQuality >= 80
                        ? 'bg-green-400'
                        : tileData.metrics.airQuality >= 60
                          ? 'bg-yellow-400'
                          : tileData.metrics.airQuality >= 40
                            ? 'bg-orange-400'
                            : 'bg-red-400'
                    }`}
                    style={{ width: `${tileData.metrics.airQuality}%` }}></div>
                </div>
              </div>

              {/* Forest Coverage */}
              <div className='space-y-2'>
                <div className='flex items-center justify-between'>
                  <span className='text-sm text-gray-300'>Forest Coverage</span>
                  <div className='flex items-center space-x-2'>
                    {getTrendIcon(tileData.trends.forestTrend)}
                    <span className='font-medium text-green-400'>{tileData.metrics.forestCoverage}%</span>
                  </div>
                </div>
                <div className='w-full bg-gray-700 rounded-full h-2'>
                  <div
                    className='h-2 rounded-full bg-green-400'
                    style={{ width: `${tileData.metrics.forestCoverage}%` }}></div>
                </div>
              </div>

              {/* NDVI Score */}
              <div className='space-y-2'>
                <div className='flex items-center justify-between'>
                  <span className='text-sm text-gray-300'>NDVI Score</span>
                  <span className='font-medium text-green-400'>{tileData.metrics.ndviScore}/100</span>
                </div>
                <div className='w-full bg-gray-700 rounded-full h-2'>
                  <div
                    className='h-2 rounded-full bg-green-400'
                    style={{ width: `${tileData.metrics.ndviScore}%` }}></div>
                </div>
              </div>

              {/* Carbon Emissions */}
              <div className='space-y-2'>
                <div className='flex items-center justify-between'>
                  <span className='text-sm text-gray-300'>Carbon Emissions (MT/year)</span>
                  <div className='flex items-center space-x-2'>
                    {getTrendIcon(tileData.trends.emissionsTrend)}
                    <span className='font-medium text-red-400'>
                      {tileData.metrics.carbonEmissions.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Temperature */}
              <div className='space-y-2'>
                <div className='flex items-center justify-between'>
                  <span className='text-sm text-gray-300'>Average Temperature</span>
                  <span className='font-medium text-white'>{tileData.metrics.temperature}°C</span>
                </div>
              </div>

              {/* Biodiversity Index */}
              <div className='space-y-2'>
                <div className='flex items-center justify-between'>
                  <span className='text-sm text-gray-300'>Biodiversity Index</span>
                  <span className='font-medium text-white'>{tileData.metrics.biodiversityIndex}/100</span>
                </div>
                <div className='w-full bg-gray-700 rounded-full h-2'>
                  <div
                    className='h-2 rounded-full bg-gray-400' // Using gray as placeholder, adjust color if needed
                    style={{ width: `${tileData.metrics.biodiversityIndex}%` }}></div>
                </div>
              </div>
            </div>

            {/* Last Updated */}
            <div className='mt-8 pt-6 border-t border-gray-700'>
              <div className='text-xs text-gray-400'>
                Last updated: {new Date(tileData.lastUpdated).toLocaleDateString()}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
