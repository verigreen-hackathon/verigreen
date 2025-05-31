import { Router } from 'express';
import { AddressController } from '../controllers/address.controller';

const router = Router();
const addressController = new AddressController();

router.post('/verify', (req, res) => addressController.verifyAddress(req, res));

export default router; 