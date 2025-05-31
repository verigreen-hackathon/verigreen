export interface AddressRequest {
  address: string;
  coordinates?: {
    latitude: number;
    longitude: number;
  };
}

export interface AddressResponse {
  id: string;
  address: string;
  coordinates: {
    latitude: number;
    longitude: number;
  };
  status: 'verified' | 'pending' | 'invalid';
  createdAt: string;
  updatedAt: string;
} 