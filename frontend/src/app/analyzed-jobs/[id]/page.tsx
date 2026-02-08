"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { api, SavedAnalysis } from "@/lib/api/client"
import { formatDateTime } from "@/lib/utils"
import {
  ArrowLeft,
  Loader2,
  Trash2,
  ExternalLink,
  CheckCircle,
  Undo2,
  Star,
} from "lucide-react"
import AnalysisDisplay from "@/components/AnalysisDisplay"

export default function AnalysisDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = Number(params.id)

  const [analysis, setAnalysis] = useState<SavedAnalysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [applied, setApplied] = useState(false)
  const [toggling, setToggling] = useState(false)

  useEffect(() => {
    async function loadAnalysis() {
      try {
        const data = await api.analyzer.get(id)
        setAnalysis(data)
        setApplied(data.applied)
      } catch {
        setError("Failed to load analysis")
      } finally {
        setLoading(false)
      }
    }
    loadAnalysis()
  }, [id])

  async function handleDelete() {
    if (!confirm("Are you sure you want to delete this analysis?")) return

    setDeleting(true)
    try {
      await api.analyzer.delete(id)
      router.push("/analyzed-jobs")
    } catch {
      setError("Failed to delete analysis")
      setDeleting(false)
    }
  }

  async function handleToggleApplied() {
    setToggling(true)
    try {
      const result = await api.analyzer.toggleApplied(id)
      setApplied(result.applied)
    } catch {
      setError("Failed to update applied status")
    } finally {
      setToggling(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    )
  }

  if (error || !analysis) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error || "Analysis not found"}
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <Link
            href="/analyzed-jobs"
            className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-2"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Analyzed Jobs
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">{analysis.job_title}</h1>
            {analysis.offers_sponsorship && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-yellow-100 border border-yellow-300 text-yellow-800 text-sm font-medium whitespace-nowrap">
                <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                Offers Sponsorship
              </span>
            )}
          </div>
          <p className="text-lg text-gray-600">{analysis.company_name}</p>
          <p className="text-sm text-gray-400 mt-1">
            Created on {formatDateTime(analysis.created_at)} · Last analyzed on {formatDateTime(analysis.last_analyzed_at)}
            {analysis.llm_model && <> · Model: {analysis.llm_model}</>}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {analysis.job_url ? (
            <a
              href={analysis.job_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-3 py-2 text-sm text-blue-600 border border-blue-200 rounded-md hover:bg-blue-50"
            >
              <ExternalLink className="w-4 h-4" />
              View Job Post
            </a>
          ) : (
            <span className="flex items-center gap-2 px-3 py-2 text-sm text-gray-400 border border-gray-200 rounded-md cursor-not-allowed">
              <ExternalLink className="w-4 h-4" />
              View Job Post
            </span>
          )}
          <button
            onClick={handleToggleApplied}
            disabled={toggling}
            className={`flex items-center gap-2 px-3 py-2 text-sm border rounded-md ${
              applied
                ? "text-orange-600 border-orange-200 hover:bg-orange-50"
                : "text-green-600 border-green-200 hover:bg-green-50"
            }`}
          >
            {toggling ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : applied ? (
              <Undo2 className="w-4 h-4" />
            ) : (
              <CheckCircle className="w-4 h-4" />
            )}
            {applied ? "I Did not Apply" : "I Applied"}
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="flex items-center gap-2 px-3 py-2 text-sm text-red-600 border border-red-200 rounded-md hover:bg-red-50"
          >
            {deleting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Trash2 className="w-4 h-4" />
            )}
            Delete
          </button>
        </div>
      </div>

      {/* Job Description (read-only) */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-semibold mb-2">Job Description</h2>
        <div className="bg-gray-50 rounded-lg p-4 max-h-48 overflow-y-auto">
          <pre className="whitespace-pre-wrap font-mono text-sm text-gray-700">
            {analysis.job_description}
          </pre>
        </div>
      </div>

      {/* Analysis Results */}
      <div className="space-y-6">
        <AnalysisDisplay analysis={analysis} />
      </div>
    </div>
  )
}
