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

export default function Home() {
  const router = useRouter()
  const [userData, setUserData] = useState<UserData | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const storedUserData = localStorage.getItem('userData')
    if (storedUserData) {
      try {
        const parsedData = JSON.parse(storedUserData) as UserData
        setUserData(parsedData)
      } catch (e) {
        console.error('Error parsing user data:', e)
      }
    }
    setIsLoading(false)
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('userData')
    localStorage.removeItem('authToken')
    setUserData(null)
    router.push('/login')
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
    return (
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Hero Section */}
        <div className="text-center space-y-6">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900">
            🏛️ Springfield Land Registry
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Official government portal for land ownership records, property verification, and registry services
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 max-w-2xl mx-auto">
            <h3 className="font-semibold text-blue-900 mb-2">🔐 Secure Access Required</h3>
            <p className="text-blue-800 text-sm mb-4">
              Access to land ownership records requires authentication. Please log in to continue.
            </p>
            <button
              onClick={() => router.push('/login')}
              className="w-full md:w-auto px-6 py-2 bg-blue-900 text-white rounded-md hover:bg-blue-800 transition-colors"
            >
              Login to Registry Portal
            </button>
          </div>
        </div>

        {/* Services Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">🔍 Property Search</h3>
            <p className="text-gray-600 text-sm">
              Search and verify land ownership records by property ID, owner name, or location.
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">📋 Ownership Verification</h3>
            <p className="text-gray-600 text-sm">
              Get official verification of property ownership with government digital seals.
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">📄 Legal Documentation</h3>
            <p className="text-gray-600 text-sm">
              Access deed information, title types, encumbrances, and legal status details.
            </p>
          </div>
        </div>

        {/* Information Section */}
        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="text-2xl font-semibold text-gray-900 mb-4">About This Registry</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Registry Authority</h4>
              <ul className="space-y-1 text-gray-600">
                <li>• Springfield Department of Land Records</li>
                <li>• State Government Property Database</li>
                <li>• County Assessor's Office Integration</li>
                <li>• Municipal Planning Department</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Available Data</h4>
              <ul className="space-y-1 text-gray-600">
                <li>• Current ownership information</li>
                <li>• Property boundaries and size</li>
                <li>• Zoning and land use details</li>
                <li>• Tax assessment records</li>
                <li>• Legal encumbrances and liens</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Dashboard Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Welcome, {userData.fullName}
            </h1>
            <p className="text-gray-600">
              Land Registry Portal Dashboard
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            Logout
          </button>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">🔍 Search Properties</h3>
          <p className="text-gray-600 text-sm mb-4">
            Find land ownership records by property ID, owner name, or location.
          </p>
          <div className="text-blue-600 text-sm font-medium">Search Records →</div>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">📋 Verify Ownership</h3>
          <p className="text-gray-600 text-sm mb-4">
            Get official verification documents for property ownership.
          </p>
          <div className="text-blue-600 text-sm font-medium">Start Verification →</div>
        </div>
        
        <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">📄 My Properties</h3>
          <p className="text-gray-600 text-sm mb-4">
            View and manage your registered property records.
          </p>
          <div className="text-blue-600 text-sm font-medium">View Properties →</div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <div>
              <p className="text-sm font-medium text-gray-900">Login Session</p>
              <p className="text-xs text-gray-500">
                {userData.loginTime ? new Date(userData.loginTime).toLocaleString() : 'Just now'}
              </p>
            </div>
            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
              Active
            </span>
          </div>
          
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <div>
              <p className="text-sm font-medium text-gray-900">Account Verification</p>
              <p className="text-xs text-gray-500">Email: {userData.email}</p>
            </div>
            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
              Verified
            </span>
          </div>
          
          <div className="flex items-center justify-between py-2">
            <div>
              <p className="text-sm font-medium text-gray-900">Registry Access</p>
              <p className="text-xs text-gray-500">Role: {userData.role?.replace('_', ' ') || 'User'}</p>
            </div>
            <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
              Authorized
            </span>
          </div>
        </div>
      </div>

      {/* System Information */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium text-gray-700">Registry Version:</span>
            <span className="ml-2 text-gray-600">v2.1</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Last Update:</span>
            <span className="ml-2 text-gray-600">January 2024</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">Session Token:</span>
            <span className="ml-2 text-gray-600 font-mono text-xs">{userData.token?.substring(0, 20)}...</span>
          </div>
          <div>
            <span className="font-medium text-gray-700">API Status:</span>
            <span className="ml-2 text-green-600">Online</span>
          </div>
        </div>
      </div>
    </div>
  )
}
