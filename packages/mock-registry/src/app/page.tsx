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

  useEffect(() => {
    const storedUserData = localStorage.getItem('userData')
    if (storedUserData) {
      try {
        const parsedData = JSON.parse(storedUserData)
        setUserData(parsedData)
      } catch (e) {
        console.error('Error parsing user data:', e)
      }
    }
  }, [])

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <section className="bg-white rounded-lg shadow-md p-8">
        {userData ? (
          <>
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Welcome back, {userData.fullName || 'User'}
            </h1>
            <p className="text-gray-600 mb-6">
              Access your land records and manage your property information through our secure government portal.
            </p>
          </>
        ) : (
          <>
            <h1 className="text-3xl font-bold text-gray-900 mb-4">Welcome to the Land Registry Portal</h1>
            <p className="text-gray-600 mb-6">
              Access official land records, property information, and registration services through our secure government portal.
            </p>
          </>
        )}
        
        {/* Search Bar */}
        <div className="max-w-2xl">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Enter property ID, address, or owner name..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button className="px-6 py-2 bg-blue-900 text-white rounded-md hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-500">
              Search
            </button>
          </div>
        </div>
      </section>

      {/* Services Grid */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold text-gray-900 mb-3">Property Search</h3>
          <p className="text-gray-600 mb-4">Search for property records, ownership history, and legal documents.</p>
          <a href="/search" className="text-blue-900 hover:text-blue-800 font-medium">Search Now →</a>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold text-gray-900 mb-3">Registration Services</h3>
          <p className="text-gray-600 mb-4">Register new properties, update ownership, or file legal documents.</p>
          <a href="/services" className="text-blue-900 hover:text-blue-800 font-medium">View Services →</a>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md">
          <h3 className="text-xl font-semibold text-gray-900 mb-3">Document Verification</h3>
          <p className="text-gray-600 mb-4">Verify the authenticity of land documents and certificates.</p>
          <a href="/verify" className="text-blue-900 hover:text-blue-800 font-medium">Verify Now →</a>
        </div>
      </section>

      {/* Announcements */}
      <section className="bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Important Announcements</h2>
        <div className="space-y-4">
          <div className="border-l-4 border-blue-900 pl-4">
            <h3 className="font-semibold text-gray-900">System Maintenance</h3>
            <p className="text-gray-600">Scheduled maintenance on Saturday, 2:00 AM - 4:00 AM</p>
          </div>
          <div className="border-l-4 border-blue-900 pl-4">
            <h3 className="font-semibold text-gray-900">New Online Services</h3>
            <p className="text-gray-600">Digital property registration now available for all districts</p>
          </div>
        </div>
      </section>

      {/* Quick Actions for logged-in users */}
      {userData && (
        <section className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button 
              onClick={() => router.push('/my-properties')}
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left"
            >
              <h3 className="font-semibold text-gray-900">My Properties</h3>
              <p className="text-gray-600">View and manage your registered properties</p>
            </button>
            <button 
              onClick={() => router.push('/documents')}
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 text-left"
            >
              <h3 className="font-semibold text-gray-900">My Documents</h3>
              <p className="text-gray-600">Access your property documents and certificates</p>
            </button>
          </div>
        </section>
      )}
    </div>
  )
}
