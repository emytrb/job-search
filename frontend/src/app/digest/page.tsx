"use client"

import { useEffect, useState } from "react"
import { api, DigestPreview } from "@/lib/api/client"
import { Mail, Send } from "lucide-react"

export default function DigestPage() {
  const [preview, setPreview] = useState<DigestPreview | null>(null)
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    loadPreview()
  }, [])

  async function loadPreview() {
    try {
      setLoading(true)
      const data = await api.digest.preview()
      setPreview(data)
    } catch {
      setError("Failed to load digest preview")
    } finally {
      setLoading(false)
    }
  }

  async function sendDigest() {
    try {
      setSending(true)
      setError(null)
      await api.digest.send()
      setSuccess("Digest sent successfully!")
      setTimeout(() => setSuccess(null), 5000)
    } catch {
      setError("Failed to send digest")
    } finally {
      setSending(false)
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Email Digest</h1>
        <button
          onClick={sendDigest}
          disabled={sending || !preview?.jobs.length}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          <Send className="w-4 h-4" />
          {sending ? "Sending..." : "Send Now"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-4">
          {success}
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-6">
          <Mail className="w-8 h-8 text-blue-600" />
          <div>
            <h2 className="text-lg font-semibold">Digest Preview</h2>
            <p className="text-sm text-gray-500">
              Preview of the next daily digest email
            </p>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500">Loading preview...</div>
        ) : !preview?.jobs.length ? (
          <div className="text-center py-8 text-gray-500">
            <p>No jobs available for digest</p>
            <p className="text-sm mt-2">Jobs will appear here once they're scraped and scored</p>
          </div>
        ) : (
          <div>
            <p className="text-sm text-gray-600 mb-4">
              {preview.job_count} job{preview.job_count !== 1 ? "s" : ""} will be included
            </p>

            <div className="space-y-3">
              {preview.jobs.map((job, index) => (
                <div
                  key={job.id}
                  className="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-gray-400 text-sm font-medium">
                      #{index + 1}
                    </span>
                    <div>
                      <p className="font-medium text-gray-900">{job.title}</p>
                      <p className="text-sm text-gray-500">{job.company}</p>
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    job.score >= 70 ? "bg-green-100 text-green-700" :
                    job.score >= 50 ? "bg-yellow-100 text-yellow-700" :
                    "bg-red-100 text-red-700"
                  }`}>
                    {job.score.toFixed(0)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-medium text-blue-900 mb-2">Automatic Digest</h3>
        <p className="text-sm text-blue-700">
          The digest is automatically sent daily at 8:00 AM UTC.
          You can also trigger it manually using the button above.
        </p>
      </div>
    </div>
  )
}
