export type Tile = {
  tile_id: number
  x: number
  y: number
  health_score: number
  ndvi: number
  coordinates: number[]
}

export type VerifierResponse = {
  forest_grid: Tile[]
  filecoin_cid: string
  processing_time: string
  timestamp: string
}
