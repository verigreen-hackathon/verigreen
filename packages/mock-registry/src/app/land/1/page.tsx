'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface UserData {
  fullName: string;
  email: string;
  token: string;
  id?: string;
  role?: string;
  loginTime?: string;
}

interface LandRecord {
  owner: {
    name: string;
    id: string;
    email: string;
    phone: string;
  };
  property: {
    id: string;
    portion_sqm: number;
    location: string;
    type: string;
    coordinates: {
      lat: number;
      lng: number;
    };
    zoning: string;
    tax_id: string;
    assessed_value: number;
  };
  verification: {
    status: string;
    timestamp: string;
    verifier_id: string;
    verification_method: string;
    last_updated: string;
  };
  legal: {
    deed_number: string;
    registration_date: string;
    title_type: string;
    encumbrances: string[];
    liens: string[];
  };
}

export default function LandPage() {
  const router = useRouter()
  const [userData, setUserData] = useState<UserData | null>(null)
  const [landRecord, setLandRecord] = useState<LandRecord | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingLandData, setIsLoadingLandData] = useState(false)

  useEffect(() => {
    const storedUserData = localStorage.getItem('userData')
    if (storedUserData) {
      try {
        const parsedData = JSON.parse(storedUserData) as UserData
        setUserData(parsedData)
        
        // Automatically fetch land data for this user
        fetchLandData(parsedData.fullName)
      } catch (e) {
        console.error('Error parsing user data:', e)
        router.push('/login')
      }
    } else {
      router.push('/login')
    }
    setIsLoading(false)
  }, [router])

  const fetchLandData = async (ownerName: string) => {
    setIsLoadingLandData(true)
    try {
      const response = await fetch(`/api/ownership/verify?owner_name=${encodeURIComponent(ownerName)}`, {
        headers: {
          'Authorization': `Bearer ${userData?.token || localStorage.getItem('authToken')}`,
          'Content-Type': 'application/json'
        },
        credentials: 'include'
      })

      if (response.ok) {
        const data = await response.json()
        setLandRecord(data)
      } else {
        console.error('Failed to fetch land data:', response.status)
      }
    } catch (error) {
      console.error('Error fetching land data:', error)
    } finally {
      setIsLoadingLandData(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('userData')
    localStorage.removeItem('authToken')
    setUserData(null)
    router.push('/login')
  }

  const generateProof = async () => {
    if (!landRecord || !userData) return
    
    try {
      // This would integrate with your vlayer notarization
      const proofUrl = `/api/ownership/verify?owner_name=${encodeURIComponent(userData.fullName)}`
      console.log('Generating proof for:', proofUrl)
      
      // For now, just show the user the URL that would be notarized
      alert(`Proof generation initiated for: ${proofUrl}`)
    } catch (error) {
      console.error('Error generating proof:', error)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-[calc(100vh-200px)] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!userData) {
    return null // Will redirect to login
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Land Ownership Record
            </h1>
            <p className="text-gray-600">
              Viewing property details for {userData.fullName}
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={() => router.push('/')}
              className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
            >
              Back to Home
            </button>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      {/* Land Record Display */}
      {isLoadingLandData ? (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-900 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading land ownership data...</p>
          </div>
        </div>
      ) : landRecord ? (
        <>
          {/* Property Overview */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex justify-between items-start mb-6">
              <h2 className="text-2xl font-semibold text-gray-900">Property Overview</h2>
              <button
                onClick={generateProof}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
              >
                🔐 Generate Ownership Proof
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-2">Property ID</h3>
                <p className="text-gray-700 font-mono">{landRecord.property.id}</p>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-2">Size</h3>
                <p className="text-gray-700">{landRecord.property.portion_sqm.toLocaleString()} sqm</p>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-2">Value</h3>
                <p className="text-gray-700">${landRecord.property.assessed_value.toLocaleString()}</p>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-2">Type</h3>
                <p className="text-gray-700 capitalize">{landRecord.property.type}</p>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-2">Zoning</h3>
                <p className="text-gray-700">{landRecord.property.zoning}</p>
              </div>
              
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-2">Status</h3>
                <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                  {landRecord.verification.status.toUpperCase()}
                </span>
              </div>
            </div>
            
            <div className="mt-6">
              <h3 className="font-semibold text-gray-900 mb-2">Location</h3>
              <p className="text-gray-700">{landRecord.property.location}</p>
            </div>
          </div>

          {/* Owner Information */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Owner Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium text-gray-900 mb-3">Contact Details</h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Name:</span>
                    <span className="ml-2 text-gray-900">{landRecord.owner.name}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">ID:</span>
                    <span className="ml-2 text-gray-900 font-mono">{landRecord.owner.id}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Email:</span>
                    <span className="ml-2 text-gray-900">{landRecord.owner.email}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Phone:</span>
                    <span className="ml-2 text-gray-900">{landRecord.owner.phone}</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="font-medium text-gray-900 mb-3">Legal Information</h3>
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Deed Number:</span>
                    <span className="ml-2 text-gray-900 font-mono">{landRecord.legal.deed_number}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Title Type:</span>
                    <span className="ml-2 text-gray-900">{landRecord.legal.title_type.replace('_', ' ')}</span>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Registration:</span>
                    <span className="ml-2 text-gray-900">{new Date(landRecord.legal.registration_date).toLocaleDateString()}</span>
                  </div>
                  {landRecord.legal.encumbrances.length > 0 && (
                    <div>
                      <span className="font-medium text-gray-700">Encumbrances:</span>
                      <span className="ml-2 text-gray-900">{landRecord.legal.encumbrances.join(', ')}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Verification Details */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">Verification Status</h2>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="text-green-800 font-semibold">PROPERTY VERIFIED</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Verified:</span>
                  <span className="ml-2 text-gray-900">{new Date(landRecord.verification.timestamp).toLocaleDateString()}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Method:</span>
                  <span className="ml-2 text-gray-900">{landRecord.verification.verification_method.replace('_', ' ')}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Verifier ID:</span>
                  <span className="ml-2 text-gray-900 font-mono">{landRecord.verification.verifier_id}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Last Updated:</span>
                  <span className="ml-2 text-gray-900">{new Date(landRecord.verification.last_updated).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Actions</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <button
                onClick={generateProof}
                className="p-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-left"
              >
                <h4 className="font-medium mb-1">🔐 Generate Proof</h4>
                <p className="text-sm opacity-90">Create blockchain proof of ownership</p>
              </button>
              
              <button
                onClick={() => window.print()}
                className="p-4 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors text-left"
              >
                <h4 className="font-medium mb-1">🖨️ Print Record</h4>
                <p className="text-sm opacity-90">Print property ownership certificate</p>
              </button>
              
              <button
                onClick={() => fetchLandData(userData.fullName)}
                className="p-4 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-left"
              >
                <h4 className="font-medium mb-1">🔄 Refresh Data</h4>
                <p className="text-sm opacity-90">Update property information</p>
              </button>
            </div>
          </div>
        </>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">No Property Records Found</h2>
            <p className="text-gray-600 mb-4">
              No land ownership records were found for {userData.fullName}.
            </p>
            <button
              onClick={() => fetchLandData(userData.fullName)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Retry Search
            </button>
          </div>
        </div>
      )}
    </div>
  )
} 