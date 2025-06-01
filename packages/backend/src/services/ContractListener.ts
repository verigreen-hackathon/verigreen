import { EVENTS_ABI } from '../abi'
import { listenerProvider } from '../config/ethers'
import { ContractListenerService } from '../contracts/ContractListenerService'

export class EventsContractListener {
  private listener: ContractListenerService

  constructor(address: string) {
    this.listener = new ContractListenerService({
      abi: EVENTS_ABI,
      address,
      provider: listenerProvider,
    })
  }

  public listenLandClaimed(
    cb: (
      owner: string,
      forestId: string,
      coordinate1: number,
      coordinate2: number,
      coordinate3: number,
      coordinate4: number
    ) => void
  ) {
    this.listener.listenToEvent('LandClaimed', (eventData) => {
      if (eventData.args?.length > 0) {
        cb(
          eventData.args[0],
          eventData.args[1],
          parseInt(eventData.args[2]),
          parseInt(eventData.args[3]),
          parseInt(eventData.args[4]),
          parseInt(eventData.args[5])
        )
      }
    })
  }

  public listenLandTilesVerified(cb: (owner: string, forestId: string, tileHash: string) => void) {
    this.listener.listenToEvent('LandTilesVerified', (eventData) => {
      cb(eventData.args[0], eventData.args[1], eventData.args[2])
    })
  }
  public listenRandomNumberGenerated(cb: (num: number, generatedNum: bigint) => void) {
    this.listener.listenToEvent('RandomNumberGenerated', (eventData) => {
      if (eventData.args?.length > 0) {
        cb(eventData.args[0], eventData.args[1])
      }
    })
  }

  public listenRandomNumberRequested(cb: (num: number, hash: string) => void) {
    this.listener.listenToEvent('RandomNumberRequested', (eventData) => {
      if (eventData.args?.length > 0) {
        cb(eventData.args[0], eventData.args[1])
      }
    })
  }
}
