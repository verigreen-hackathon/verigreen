import { Request, Response } from 'express'
import { SubmissionService } from '../services/SubmissionService'
import { isAddress } from 'ethers'

export class SubmissionsController {
  private submissionService: SubmissionService

  constructor() {
    this.submissionService = new SubmissionService()
  }

  async getWalletSubmissions(req: Request, res: Response) {
    try {
      const wallet_address = req.query['wallet_address'] as string

      if (!wallet_address || wallet_address === '' || isAddress(wallet_address)) {
        res.status(400).json({ success: false, message: 'wallet_adddress field is required!', data: null })
        return
      }

      const data = await this.submissionService.getSubmissionsByOwner(wallet_address)

      res.status(200).json({ success: true, message: null, data })
      return
    } catch (error) {
      console.error(error)
      res.status(500).json({ success: false, message: 'Internal error occured!', data: null })
      return
    }
  }
}
