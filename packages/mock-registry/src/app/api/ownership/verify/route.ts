import { NextRequest, NextResponse } from 'next/server';

// Mock land ownership database
const landRecords = [
  {
    owner: {
      name: "AliceJohnson",
      id: "GOV123456789",
      email: "alice.johnson@email.com",
      phone: "+1-555-0123"
    },
    property: {
      id: "LAND-PARCEL-001",
      portion_sqm: 5000,
      location: "123 Green Valley Road, Springfield, State 12345",
      type: "residential",
      coordinates: {
        lat: 40.7128,
        lng: -74.0060
      },
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
      coordinates: {
        lat: 40.7589,
        lng: -73.9851
      },
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
  },
  {
    owner: {
      name: "Maria Garcia",
      id: "GOV555666777",
      email: "maria.garcia@email.com", 
      phone: "+1-555-0789"
    },
    property: {
      id: "LAND-PARCEL-003",
      portion_sqm: 8500,
      location: "789 Farmland Drive, Springfield, State 12345",
      type: "agricultural",
      coordinates: {
        lat: 40.6892,
        lng: -74.0445
      },
      zoning: "A-1 Agricultural",
      tax_id: "TAX-2024-003",
      assessed_value: 320000
    },
    verification: {
      status: "verified",
      timestamp: "2024-01-25T09:15:00Z",
      verifier_id: "VERIFIER-001",
      verification_method: "survey_update",
      last_updated: "2024-01-25T09:15:00Z"
    },
    legal: {
      deed_number: "DEED-2024-003",
      registration_date: "2024-01-20T00:00:00Z",
      title_type: "fee_simple",
      encumbrances: ["agricultural_restriction"],
      liens: []
    }
  }
];

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const propertyId = searchParams.get('property_id');
  const ownerId = searchParams.get('owner_id');
  const ownerName = searchParams.get('owner_name');

  // Simulate authentication check
  const authHeader = request.headers.get('authorization');
  const sessionToken = request.cookies.get('session_token')?.value;
  
  if (!authHeader && !sessionToken) {
    return NextResponse.json(
      { 
        error: 'Unauthorized', 
        message: 'Valid authentication required to access land records',
        code: 'AUTH_REQUIRED'
      }, 
      { status: 401 }
    );
  }

  // Add CORS headers for development
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Content-Type': 'application/json',
    'X-Government-API': 'Springfield Land Registry v2.1',
    'X-Response-Time': new Date().toISOString(),
    'Cache-Control': 'no-cache, no-store, must-revalidate'
  };

  try {
    let record = null;

    // Search by property ID
    if (propertyId) {
      record = landRecords.find(r => r.property.id === propertyId);
    }
    // Search by owner ID  
    else if (ownerId) {
      record = landRecords.find(r => r.owner.id === ownerId);
    }
    // Search by owner name
    else if (ownerName) {
      record = landRecords.find(r => 
        r.owner.name.toLowerCase().includes(ownerName.toLowerCase())
      );
    }
    // Default to first record if no search params (for demo)
    else {
      record = landRecords[0];
    }

    if (!record) {
      return NextResponse.json(
        { 
          error: 'Record not found',
          message: 'No land ownership record found for the provided criteria',
          code: 'RECORD_NOT_FOUND'
        }, 
        { 
          status: 404,
          headers 
        }
      );
    }

    // Add request tracking (for verification purposes)
    const response = {
      ...record,
      request_info: {
        timestamp: new Date().toISOString(),
        request_id: `REQ-${Date.now()}`,
        api_version: '2.1',
        source_ip: request.headers.get('x-forwarded-for') || 'unknown',
        user_agent: request.headers.get('user-agent') || 'unknown'
      },
      government_seal: {
        authority: "Springfield Department of Land Records",
        digital_signature: "SHA256:a1b2c3d4e5f6...",
        certificate_authority: "State Government Root CA",
        issued_at: new Date().toISOString()
      }
    };

    return NextResponse.json(response, { 
      status: 200,
      headers 
    });

  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error',
        message: 'An error occurred while processing your request',
        code: 'INTERNAL_ERROR'
      }, 
      { 
        status: 500,
        headers 
      }
    );
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
} 