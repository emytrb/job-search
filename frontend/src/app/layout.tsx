import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Job Searcher",
  description: "Automated job search and analysis",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-50">
          <nav className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex items-center">
                  <a href="/" className="text-xl font-bold text-blue-600">
                    Job Searcher
                  </a>
                  <div className="hidden md:flex ml-10 space-x-8">
                    <a href="/" className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium">
                      Jobs
                    </a>
                    <a href="/analyzer" className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium">
                      Analyzer
                    </a>
                    <a href="/analyzed-jobs" className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium">
                      Analyzed Jobs
                    </a>
                    <a href="/sources" className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium">
                      Sources
                    </a>
                    <a href="/digest" className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium">
                      Digest
                    </a>
                    <a href="/settings" className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium">
                      Settings
                    </a>
                  </div>
                </div>
              </div>
            </div>
          </nav>
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
