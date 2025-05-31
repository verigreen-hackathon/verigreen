'use client'

import { useState, useEffect } from 'react'
import { CardList } from '@/components/CardList'
import { SITE_DESCRIPTION, SITE_NAME, SITE_EMOJI } from '@/utils/site'

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
  request_info?: {
    timestamp: string;
    request_id: string;
    api_version: string;
    source_ip: string;
    user_agent: string;
  };
  government_seal?: {
    authority: string;
    digital_signature: string;
    certificate_authority: string;
    issued_at: string;
  };
}

// Mock land ownership database
const mockLandRecords: LandRecord[] = [
  {
    owner: {
      name: "Alice Johnson",
      id: "GOV123456789",
      email: "alice.johnson@email.com",
      phone: "+1-555-0123"
    },
    property: {
      id: "LAND-PARCEL-001",
      portion_sqm: 5000,
      location: "123 Green Valley Road, Springfield, State 12345",
      type: "residential",
      coordinates: { lat: 40.7128, lng: -74.0060 },
      zoning: "R-1 Residential",
      tax_id: "TAX-2024-001",
      assessed_value: 450000
    },
    verification: {
      status: "verified",
      timestamp: "2024-01-15T10:30:00Z",
      verifier_id: "VERIFIER-001",
      verification_method: "physical_inspection",
      last_updated: "2024-01-15T10:30:00Z"
    },
    legal: {
      deed_number: "DEED-2024-001",
      registration_date: "2024-01-10T00:00:00Z",
      title_type: "fee_simple",
      encumbrances: [],
      liens: []
    }
  },
  {
    owner: {
      name: "Bob Smith",
      id: "GOV987654321", 
      email: "bob.smith@email.com",
      phone: "+1-555-0456"
    },
    property: {
      id: "LAND-PARCEL-002",
      portion_sqm: 3200,
      location: "456 Oak Street, Springfield, State 12345",
      type: "commercial",
      coordinates: { lat: 40.7589, lng: -73.9851 },
      zoning: "C-1 Commercial",
      tax_id: "TAX-2024-002",
      assessed_value: 750000
    },
    verification: {
      status: "verified",
      timestamp: "2024-01-20T14:45:00Z",
      verifier_id: "VERIFIER-002",
      verification_method: "document_review",
      last_updated: "2024-01-20T14:45:00Z"
    },
    legal: {
      deed_number: "DEED-2024-002",
      registration_date: "2024-01-15T00:00:00Z",
      title_type: "fee_simple",
      encumbrances: ["easement_utility"],
      liens: []
    }
  }
];

export default function Home() {
  const [selectedOwner, setSelectedOwner] = useState<string>('Alice Johnson')
  const [landRecord, setLandRecord] = useState<LandRecord | null>(null)
  const [loading, setLoading] = useState(false)
  const [proofStatus, setProofStatus] = useState<'idle' | 'generating' | 'generated' | 'verified'>('idle')
  const [proofData, setProofData] = useState<any>(null)
  const [showVerificationReport, setShowVerificationReport] = useState(false)

  useEffect(() => {
    const record = mockLandRecords.find(r => r.owner.name === selectedOwner)
    setLandRecord(record || null)
  }, [selectedOwner])

  const generateVlayerProof = async () => {
    if (!landRecord) return

    setLoading(true)
    setProofStatus('generating')

    try {
      // Simulate vlayer proof generation
      await new Promise(resolve => setTimeout(resolve, 2000))

      const mockProof = {
        proof: "0x" + "a".repeat(128),
        ownerName: landRecord.owner.name,
        landId: landRecord.property.id,
        landPortion: landRecord.property.portion_sqm,
        account: "0x1234567890123456789012345678901234567890",
        timestamp: new Date().toISOString()
      }

      setProofData(mockProof)
      setProofStatus('generated')

      // Trigger vlayer extension detection
      window.dispatchEvent(new CustomEvent('vlayer-capture-ready', {
        detail: {
          url: `${window.location.origin}/api/ownership/verify`,
          data: landRecord
        }
      }))

    } catch (error) {
      console.error('Error generating proof:', error)
      setProofStatus('idle')
    } finally {
      setLoading(false)
    }
  }

  const verifyOnChain = async () => {
    if (!proofData) return

    setLoading(true)
    try {
      // Simulate on-chain verification
      await new Promise(resolve => setTimeout(resolve, 1500))
      setProofStatus('verified')
    } catch (error) {
      console.error('Error verifying on-chain:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-gray-900 flex items-center justify-center gap-3">
          {SITE_EMOJI} {SITE_NAME}
        </h1>
        <p className="text-xl text-gray-600">{SITE_DESCRIPTION}</p>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-2xl mx-auto">
          <h3 className="font-semibold text-blue-900 mb-2">🔗 vlayer Web Proofs Integration</h3>
          <p className="text-blue-800 text-sm">
            Verify land ownership using cryptographic proofs from government registries. 
            Generate ZK proofs and mint verifiable NFTs on Optimism Sepolia.
          </p>
        </div>
      </div>

      {/* Owner Selection */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Land Ownership Verification</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Property Owner
            </label>
            <select
              value={selectedOwner}
              onChange={(e) => setSelectedOwner(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {mockLandRecords.map((record) => (
                <option key={record.owner.id} value={record.owner.name}>
                  {record.owner.name} - {record.property.id}
                </option>
              ))}
            </select>
          </div>

          {landRecord && (
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Property:</span>
                  <p className="text-gray-900">{landRecord.property.id}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Size:</span>
                  <p className="text-gray-900">{landRecord.property.portion_sqm.toLocaleString()} sqm</p>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Status:</span>
                  <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                    {landRecord.verification.status.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* vlayer Proof Generation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Proof Generation Panel */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Generate vlayer Proof</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <h4 className="font-medium text-gray-900">Web Proof Generation</h4>
                <p className="text-sm text-gray-600">Create cryptographic proof from government registry</p>
              </div>
              <div className="text-right">
                {proofStatus === 'idle' && (
                  <button
                    onClick={generateVlayerProof}
                    disabled={!landRecord || loading}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                  >
                    Generate Proof
                  </button>
                )}
                {proofStatus === 'generating' && (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    <span className="text-sm text-blue-600">Generating...</span>
                  </div>
                )}
                {proofStatus === 'generated' && (
                  <span className="text-sm text-green-600 font-medium">✓ Proof Generated</span>
                )}
                {proofStatus === 'verified' && (
                  <span className="text-sm text-green-600 font-medium">✓ Verified On-Chain</span>
                )}
              </div>
            </div>

            {proofData && (
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h4 className="font-medium text-green-900 mb-2">Proof Generated Successfully</h4>
                  <div className="text-sm space-y-2">
                    <div>
                      <span className="font-medium">Owner:</span> {proofData.ownerName}
                    </div>
                    <div>
                      <span className="font-medium">Land ID:</span> {proofData.landId}
                    </div>
                    <div>
                      <span className="font-medium">Land Portion:</span> {proofData.landPortion} sqm
                    </div>
                    <div>
                      <span className="font-medium">Account:</span> {proofData.account}
                    </div>
                  </div>
                </div>

                {proofStatus === 'generated' && (
                  <button
                    onClick={verifyOnChain}
                    disabled={loading}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
                  >
                    {loading ? 'Verifying...' : 'Verify On-Chain & Mint NFT'}
                  </button>
                )}

                {proofStatus === 'verified' && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h4 className="font-medium text-blue-900 mb-2">🎉 Land Ownership NFT Minted!</h4>
                    <p className="text-sm text-blue-800">
                      Your land ownership has been verified on-chain and an NFT has been minted to your wallet.
                    </p>
                    <a 
                      href={`https://sepolia-optimism.etherscan.io/address/${proofData.account}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-block mt-2 text-sm text-blue-600 hover:text-blue-800 underline"
                    >
                      View on Optimism Sepolia Explorer →
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Verification Report */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-semibold text-gray-900">Verification Report</h3>
            <button
              onClick={() => setShowVerificationReport(!showVerificationReport)}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              {showVerificationReport ? 'Hide Details' : 'Show Details'}
            </button>
          </div>

          {landRecord && showVerificationReport && (
            <div className="space-y-4">
              {/* Owner Information */}
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Owner Information</h4>
                <div className="bg-gray-50 rounded-lg p-3 text-sm" id="vlayer-owner-data">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <span className="font-medium">Name:</span> {landRecord.owner.name}
                    </div>
                    <div>
                      <span className="font-medium">ID:</span> {landRecord.owner.id}
                    </div>
                  </div>
                </div>
              </div>

              {/* Property Information */}
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Property Information</h4>
                <div className="bg-gray-50 rounded-lg p-3 text-sm" id="vlayer-property-data">
                  <div className="space-y-1">
                    <div><span className="font-medium">ID:</span> {landRecord.property.id}</div>
                    <div><span className="font-medium">Size:</span> {landRecord.property.portion_sqm} sqm</div>
                    <div><span className="font-medium">Location:</span> {landRecord.property.location}</div>
                    <div><span className="font-medium">Type:</span> {landRecord.property.type}</div>
                  </div>
                </div>
              </div>

              {/* Verification Status */}
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Verification Status</h4>
                <div className="bg-green-50 border border-green-200 rounded-lg p-3" id="vlayer-verification-data">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-green-800 font-semibold text-sm">VERIFIED</span>
                  </div>
                  <div className="text-sm text-gray-600">
                    Verified: {new Date(landRecord.verification.timestamp).toLocaleDateString()}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Technical Details */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Technical Implementation</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">vlayer Web Proofs Workflow</h4>
            <ul className="space-y-1 text-gray-600">
              <li>1. Browser extension captures government registry data</li>
              <li>2. TLS Notary provides cryptographic proof of web data</li>
              <li>3. GreenWebProofProver generates ZK proof off-chain</li>
              <li>4. GreenWebVerifier verifies proof on Optimism Sepolia</li>
              <li>5. Land ownership NFT minted upon successful verification</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Smart Contracts</h4>
            <ul className="space-y-1 text-gray-600">
              <li>• <code>GreenWebProofProver.sol</code> - Off-chain proof generation</li>
              <li>• <code>GreenWebVerifier.sol</code> - On-chain ERC721 verification</li>
              <li>• Network: Optimism Sepolia (Chain ID: 11155420)</li>
              <li>• Integration: vlayer SDK + Foundry deployment</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
