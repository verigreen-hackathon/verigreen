import { EnsPlugin, JsonRpcProvider, Network } from 'ethers'

export const signerProvider = new JsonRpcProvider('https://sepolia.optimism.io')
export const listenerProvider = new JsonRpcProvider(
  'https://opt-sepolia.g.alchemy.com/v2/wcZgbA61qd5hiLkcaa_8j83RHzyAFUUL'
)
