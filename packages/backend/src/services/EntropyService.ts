import { Wallet, Contract, parseEther, randomBytes } from 'ethers'
import { ENTROPY_ABI } from '../abi'
import { signerProvider } from '../config/ethers'
import { EventsContractListener } from './ContractListener'
import { ENTROPY_FEE } from '../constants'

export class EntropyService {
  private listener: EventsContractListener
  private entropy: Contract

  private numberHashes = new Map()

  constructor() {
    this.listener = new EventsContractListener(process.env.ENTROPY_ADDRESS as string)
    const wallet = new Wallet(process.env.PRIVATE_KEY as string, signerProvider)
    this.entropy = new Contract(process.env.ENTROPY_ADDRESS as string, ENTROPY_ABI, wallet)
  }
  async getRandomNumber(maxValue: number) {
    const userRandomNumber = randomBytes(32)
    this.numberHashes.set(userRandomNumber, -1)

    await this.entropy.requestRandomNumber(userRandomNumber, maxValue, {
      value: ENTROPY_FEE,
    })
    return await this.startListenersAndGetNumber()
  }

  deriveNumbers(generatedNumber: number, count: number): number[] {
    const derivedNumbers = []

    for (let index = 0; index < count; index++) {
      const random = Math.floor(Math.random() * 1000)

      derivedNumbers.push(random % generatedNumber)
    }
    return derivedNumbers
  }

  async startListenersAndGetNumber() {
    return new Promise<number>((resolve, reject) => {
      this.listener.listenRandomNumberGenerated((num, generatedNum) => {
        resolve(parseInt(generatedNum.toString()))
      })
    })
  }
}
