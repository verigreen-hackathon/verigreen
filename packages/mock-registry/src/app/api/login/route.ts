import { NextRequest, NextResponse } from 'next/server';

// Mock user database
const users = [
  {
    id: '1',
    email: 'alice.johnson@email.com',
    password: 'password123',
    fullName: 'Alice Johnson',
    role: 'property_owner',
    phone: '+1-555-0123'
  },
  {
    id: '2', 
    email: 'bob.smith@email.com',
    password: 'password123',
    fullName: 'Bob Smith',
    role: 'property_owner',
    phone: '+1-555-0456'
  },
  {
    id: '3',
    email: 'maria.garcia@email.com',
    password: 'password123',
    fullName: 'Maria Garcia',
    role: 'property_owner',
    phone: '+1-555-0789'
  },
  {
    id: '4',
    email: 'demo@example.com',
    password: 'demo',
    fullName: 'Demo User',
    role: 'demo_user',
    phone: '+1-555-DEMO'
  },
  {
    id: '5',
    email: 'admin@registry.gov',
    password: 'admin123',
    fullName: 'Registry Administrator',
    role: 'admin',
    phone: '+1-555-ADMIN'
  }
];

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json();

    // Validate input
    if (!email || !password) {
      return NextResponse.json(
        { 
          error: 'Missing credentials',
          message: 'Email and password are required',
          code: 'MISSING_CREDENTIALS'
        },
        { status: 400 }
      );
    }

    // Find user
    const user = users.find(u => u.email.toLowerCase() === email.toLowerCase());
    
    if (!user) {
      return NextResponse.json(
        { 
          error: 'Invalid credentials',
          message: 'No account found with this email address',
          code: 'INVALID_EMAIL'
        },
        { status: 401 }
      );
    }

    // Check password
    if (user.password !== password) {
      return NextResponse.json(
        { 
          error: 'Invalid credentials',
          message: 'Incorrect password',
          code: 'INVALID_PASSWORD'
        },
        { status: 401 }
      );
    }

    // Generate mock JWT token
    const token = `mock_jwt_${user.id}_${Date.now()}`;
    
    // Create response with user data
    const responseData = {
      token,
      fullName: user.fullName,
      email: user.email,
      id: user.id,
      role: user.role,
      phone: user.phone,
      loginTime: new Date().toISOString(),
      expiresIn: '24h'
    };

    // Create response
    const response = NextResponse.json(responseData, { 
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
      }
    });

    // Set secure session cookie
    response.cookies.set('session_token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 60 * 60 * 24 // 24 hours
    });

    return response;

  } catch (error) {
    console.error('Login API Error:', error);
    return NextResponse.json(
      { 
        error: 'Internal server error',
        message: 'An error occurred during login',
        code: 'SERVER_ERROR'
      },
      { status: 500 }
    );
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
} 