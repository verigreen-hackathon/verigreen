import { AbiCoder, Contract, keccak256, Wallet } from 'ethers'
import { EventsContractListener } from './ContractListener'
import { signerProvider } from '../config/ethers'
import { VERI_GREEN_ABI } from '../abi'
import { EntropyService } from './EntropyService'
import { VerifierService } from './VerifierService'
import { prisma } from '../config/prisma'

export class VeriGreenService {
  private listener: EventsContractListener
  private contract: Contract
  private entropyService: EntropyService
  private verifierService: VerifierService

  constructor(entropyService_: EntropyService, verifierService_: VerifierService) {
    this.listener = new EventsContractListener(process.env.ENTROPY_ADDRESS as string)
    const wallet = new Wallet(process.env.PRIVATE_KEY as string, signerProvider)
    this.contract = new Contract(process.env.ENTROPY_ADDRESS as string, VERI_GREEN_ABI, wallet)
    this.entropyService = entropyService_
    this.verifierService = verifierService_
  }

  async verifyClaim(
    owner: string,
    forestId: string,
    coordinate1: number,
    coordinate2: number,
    coordinate3: number,
    coordinate4: number
  ) {
    try {
      const coordinates = [coordinate1, coordinate2, coordinate3, coordinate4]

      const verifierResponse = await this.verifierService.getTiles(
        [coordinate1, coordinate2, coordinate3, coordinate4],
        owner
      )

      const randomNumber = await this.entropyService.getRandomNumber(verifierResponse.forest_grid.length)

      const indexes = this.entropyService.deriveNumbers(randomNumber, 7)

      const valid = this.verifierService.checkGreennes(indexes, verifierResponse.forest_grid)
      let transactionHash = ''
      let tileHash = ''
      if (valid) {
        tileHash = keccak256(
          AbiCoder.defaultAbiCoder().encode(
            ['string', 'string', 'string', 'string'],
            [coordinate1.toString(), coordinate2.toString(), coordinate3.toString(), coordinate4.toString()]
          )
        )
        const tx = await this.contract.verifyTilesInLand(owner, forestId, tileHash)
        await tx.wait()
        transactionHash = tx.hash
      }

      await prisma.submission.create({
        data: {
          user_address: owner,
          coordinates,
          selectedTiles: indexes,
          tileHash,
          valid,
          transactionHash,
          generatedRandomNumber: randomNumber,
          verifierResponse: {
            create: {
              forest_grid: verifierResponse.forest_grid,
              filecoin_cid: verifierResponse.filecoin_cid,
              processing_time: verifierResponse.processing_time,
              timestamp: verifierResponse.timestamp,
            },
          },
        },
      })
    } catch (error) {
      console.error(error)
    }
  }

  startListeningLandClaim() {
    this.listener.listenLandClaimed(async (owner, forestId, coordinate1, coordinate2, coordinate3, coordinate4) => {
      this.verifyClaim(owner, forestId, coordinate1, coordinate2, coordinate3, coordinate4)
        .then(() => {})
        .catch(console.error)

      prisma.claim
        .create({
          data: {
            forest_id: forestId,
            user_address: owner,
            coordinates: [coordinate1, coordinate2, coordinate3, coordinate4],
          },
        })
        .then(() => {})
        .catch(console.error)
    })
  }
}
