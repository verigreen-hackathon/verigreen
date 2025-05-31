import { NextRequest, NextResponse } from 'next/server';

// Mock user database
const mockUsers = [
  {
    email: 'alice.johnson@email.com',
    password: 'password123',
    fullName: 'Alice Johnson',
    id: 'GOV123456789',
    role: 'property_owner'
  },
  {
    email: 'bob.smith@email.com', 
    password: 'password123',
    fullName: 'Bob Smith',
    id: 'GOV987654321',
    role: 'property_owner'
  },
  {
    email: 'demo@example.com',
    password: 'demo',
    fullName: 'Demo User',
    id: 'DEMO123',
    role: 'demo'
  }
];

export async function POST(request: NextRequest) {
  console.log('🔐 Login API route hit!');
  
  try {
    const body = await request.json();
    console.log('📧 Login request received:', { email: body.email, password: '***' });
    
    const { email, password } = body;

    // Find user in mock database
    const user = mockUsers.find(u => u.email === email && u.password === password);

    if (!user) {
      console.log('❌ Invalid credentials for:', email);
      return NextResponse.json(
        { 
          error: 'Invalid credentials', 
          message: 'Email or password is incorrect',
          code: 'INVALID_CREDENTIALS'
        }, 
        { status: 401 }
      );
    }

    console.log('✅ User found:', user.fullName);

    // Generate mock session token
    const token = `mock_token_${Date.now()}`;
    
    // Create response data
    const responseData = {
      token,
      fullName: user.fullName,
      email: user.email,
      id: user.id,
      role: user.role,
      loginTime: new Date().toISOString()
    };

    console.log('📤 Sending response:', responseData);

    return NextResponse.json(responseData, { 
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Set-Cookie': `session_token=${token}; Path=/; HttpOnly; SameSite=Strict`
      }
    });

  } catch (error) {
    console.error('💥 Login API Error:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error',
        message: 'An error occurred during login',
        code: 'INTERNAL_ERROR'
      }, 
      { status: 500 }
    );
  }
}

export async function OPTIONS() {
  console.log('🔄 OPTIONS request to login API');
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
} 