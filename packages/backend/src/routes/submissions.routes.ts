import { Router } from 'express'
import { SubmissionsController } from '../controllers/submission.controller'

const router = Router()
const submissionController = new SubmissionsController()

router.get('/submissions', (req, res) => submissionController.getWalletSubmissions(req, res))

export default router
