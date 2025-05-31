import { Request, Response } from 'express';
import { AddressRequest, AddressResponse } from '../types/address.types';
import { AddressService } from '../services/address.service';

export class AddressController {
  private addressService: AddressService;

  constructor() {
    this.addressService = AddressService.getInstance();
  }

  private validateAddressRequest(data: any): data is AddressRequest {
    if (!data || typeof data !== 'object') {
      return false;
    }

    if (!data.address || typeof data.address !== 'string') {
      return false;
    }

    if (data.coordinates) {
      if (
        typeof data.coordinates.latitude !== 'number' ||
        typeof data.coordinates.longitude !== 'number'
      ) {
        return false;
      }
    }

    return true;
  }

  async verifyAddress(req: Request, res: Response): Promise<void> {
    try {
      const body = req.body;

      if (!this.validateAddressRequest(body)) {
        res.status(400).json({ error: 'Invalid request body' });
        return;
      }

      const result = await this.addressService.verifyAddress(body);
      res.json(result);
    } catch (error) {
      console.error('Error in address controller:', error);
      res.status(500).json({ error: 'Internal server error' });
    }
  }
} 