import { AddressRequest, AddressResponse } from '../types/address.types';
import { Contract, ethers } from 'ethers';

// Mock API response interface
interface MockApiResponse {
  status: 'success' | 'error';
  data: {
    verified: boolean;
    confidence: number;
    metadata: {
      city: string;
      state: string;
      country: string;
      postalCode: string;
    };
  };
}


// Smart contract ABI for address verification
const ADDRESS_VERIFICATION_ABI = [
  "function verifyAddress(string memory _address, uint256 _latitude, uint256 _longitude) public returns (bool)",
  "function getVerificationStatus(string memory _address) public view returns (bool)",
  "event AddressVerified(address indexed verifier, string indexed addressHash, bool status)"
];

export class AddressService {
  private static instance: AddressService;
  private provider: ethers.JsonRpcProvider;
  private contract: Contract;

  private constructor() {
    // Initialize provider and contract
    // Get signer from private key
    this.provider = new ethers.JsonRpcProvider(process.env.RPC_URL || 'http://localhost:8545');
    const signer = new ethers.Wallet(
        process.env.PRIVATE_KEY || '',
        this.provider
      );
      
    this.contract = new ethers.Contract(
      process.env.ADDRESS_VERIFICATION_CONTRACT || '',
      ADDRESS_VERIFICATION_ABI,
      signer
    );
  }

  public static getInstance(): AddressService {
    if (!AddressService.instance) {
      AddressService.instance = new AddressService();
    }
    return AddressService.instance;
  }

  private async mockApiRequest(address: string): Promise<MockApiResponse> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Mock response
    return {
      status: 'success',
      data: {
        verified: true,
        confidence: 0.95,
        metadata: {
          city: 'New York',
          state: 'NY',
          country: 'USA',
          postalCode: '10001'
        }
      }
    };
  }

  private async verifyOnChain(
    address: string,
    latitude: number,
    longitude: number
  ): Promise<boolean> {
    try {
      // Convert coordinates to uint256 (multiply by 1e6 to preserve decimal places)
      const latUint = Math.floor(latitude * 1e6);
      const longUint = Math.floor(longitude * 1e6);
      
      // Send transaction
      const tx = await this.contract.verifyAddress(
        address,
        latUint,
        longUint
      );

      // Wait for transaction to be mined
      const receipt = await tx.wait();

      // Check if transaction was successful
      if (receipt.status === 1) {
        // Get verification status
        const isVerified = await this.contract.getVerificationStatus(address);
        return isVerified;
      }

      return false;
    } catch (error) {
      console.error('Error in on-chain verification:', error);
      throw error;
    }
  }

  async verifyAddress(data: AddressRequest): Promise<AddressResponse> {
    try {
      // Step 1: Mock API request
      const apiResponse = await this.mockApiRequest(data.address);
      
      if (apiResponse.status !== 'success' || !apiResponse.data.verified) {
        throw new Error('Address verification failed in API check');
      }

      // Step 2: On-chain verification
      const coordinates = data.coordinates || { latitude: 0, longitude: 0 };
      const isVerifiedOnChain = await this.verifyOnChain(
        data.address,
        coordinates.latitude,
        coordinates.longitude
      );

      // Step 3: Prepare response
      const response: AddressResponse = {
        id: Math.random().toString(36).substring(7),
        address: data.address,
        coordinates: coordinates,
        status: isVerifiedOnChain ? 'verified' : 'invalid',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      return response;
    } catch (error) {
      console.error('Error verifying address:', error);
      throw error;
    }
  }
} 