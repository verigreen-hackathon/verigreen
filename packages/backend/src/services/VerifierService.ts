import axios from 'axios'
import { Tile, VerifierResponse } from '../types/verifier.types'

export class VerifierService {
  async getTiles(bounding_box: number[], wallet_address: string) {
    const response = await axios.post<VerifierResponse>(process.env.VERIFIER_URL as string, {
      bounding_box,
      wallet_address,
    })

    return response.data
  }

  checkGreennes(indexes: number[], tiles: Tile[]): boolean {
    let valid = true

    for (let index = 0; index < indexes.length; index++) {
      let tileIndex = indexes[index]
      if (tileIndex > tiles.length) {
        tileIndex = tileIndex % tiles.length
      }

      valid = valid && tiles[index].health_score > 0.57
    }

    return valid
  }
}
