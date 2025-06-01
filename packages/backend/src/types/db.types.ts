import { VerifierResponse } from './verifier.types'

export type Submission = {
  id?: string
  user_address: string
  coordinates: number[]
  selectedTiles: number[]
  tileHash: string
  valid: boolean
  transactionHash: string
  randomNumber: number
  verifierResponse: VerifierResponse
}
