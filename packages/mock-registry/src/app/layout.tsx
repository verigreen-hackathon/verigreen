import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Link from "next/link";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Land Registry Portal",
  description: "Official Government Land Registry Portal",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen flex flex-col bg-gray-50`}>
        <header className="bg-blue-900 text-white py-4">
          <div className="container mx-auto px-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <Link href="/" className="text-2xl font-bold">Land Registry Portal</Link>
                <div className="text-sm">Official Government Portal</div>
              </div>
              <div className="flex items-center space-x-6">
                <nav className="hidden md:flex space-x-6">
                  <a href="#" className="hover:text-blue-200">Home</a>
                  <a href="#" className="hover:text-blue-200">Search Records</a>
                  <a href="#" className="hover:text-blue-200">Services</a>
                  <a href="#" className="hover:text-blue-200">Contact</a>
                </nav>
                <a 
                  href="/login" 
                  className="px-4 py-2 bg-white text-blue-900 rounded-md hover:bg-blue-50 transition-colors duration-200 font-medium"
                >
                  Login
                </a>
              </div>
            </div>
          </div>
        </header>

        <main className="flex-grow container mx-auto px-4 py-8">
          {children}
        </main>

        <footer className="bg-gray-800 text-white py-6">
          <div className="container mx-auto px-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div>
                <h3 className="text-lg font-semibold mb-4">Contact Information</h3>
                <p>Government Land Registry Office</p>
                <p>123 Official Street</p>
                <p>City, State 12345</p>
              </div>
              <div>
                <h3 className="text-lg font-semibold mb-4">Quick Links</h3>
                <ul className="space-y-2">
                  <li><a href="/about" className="hover:text-blue-200">About Us</a></li>
                  <li><a href="/faq" className="hover:text-blue-200">FAQ</a></li>
                  <li><a href="/privacy" className="hover:text-blue-200">Privacy Policy</a></li>
                </ul>
              </div>
              <div>
                <h3 className="text-lg font-semibold mb-4">Office Hours</h3>
                <p>Monday - Friday: 9:00 AM - 5:00 PM</p>
                <p>Saturday: 9:00 AM - 1:00 PM</p>
                <p>Sunday: Closed</p>
              </div>
            </div>
            <div className="mt-8 pt-6 border-t border-gray-700 text-center">
              <p>&copy; {new Date().getFullYear()} Government Land Registry. All rights reserved.</p>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
