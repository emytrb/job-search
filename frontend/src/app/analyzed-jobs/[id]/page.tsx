"use client"

import { useState, useEffect, useMemo } from "react"
import { useParams, useRouter } from "next/navigation"
import Link from "next/link"
import { api, SavedAnalysis } from "@/lib/api/client"
import {
  ArrowLeft,
  Copy,
  Check,
  Loader2,
  XCircle,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  Trash2,
  ExternalLink,
} from "lucide-react"

export default function AnalysisDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = Number(params.id)

  const [analysis, setAnalysis] = useState<SavedAnalysis | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set())
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    async function loadAnalysis() {
      try {
        const data = await api.analyzer.get(id)
        setAnalysis(data)
      } catch {
        setError("Failed to load analysis")
      } finally {
        setLoading(false)
      }
    }
    loadAnalysis()
  }, [id])

  function copyToClipboard() {
    if (analysis?.cover_letter) {
      navigator.clipboard.writeText(analysis.cover_letter)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

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

  function getScoreColor(score: number) {
    if (score >= 80) return "text-green-600 bg-green-50 border-green-200"
    if (score >= 60) return "text-yellow-600 bg-yellow-50 border-yellow-200"
    return "text-red-600 bg-red-50 border-red-200"
  }

  function getImportanceColor(importance: string) {
    switch (importance.toLowerCase()) {
      case "required":
        return "bg-red-100 text-red-700"
      case "preferred":
        return "bg-yellow-100 text-yellow-700"
      default:
        return "bg-gray-100 text-gray-700"
    }
  }

  // Group suggestions by section
  const groupedSuggestions = useMemo(() => {
    if (!analysis?.resume_suggestions) return {}
    return analysis.resume_suggestions.reduce((acc, suggestion) => {
      const section = suggestion.section
      if (!acc[section]) {
        acc[section] = []
      }
      acc[section].push(suggestion)
      return acc
    }, {} as Record<string, typeof analysis.resume_suggestions>)
  }, [analysis?.resume_suggestions])

  function toggleSection(section: string) {
    setExpandedSections((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(section)) {
        newSet.delete(section)
      } else {
        newSet.add(section)
      }
      return newSet
    })
  }

  function expandAllSections() {
    setExpandedSections(new Set(Object.keys(groupedSuggestions)))
  }

  function collapseAllSections() {
    setExpandedSections(new Set())
  }

  function formatDate(dateString: string) {
    const date = new Date(dateString)
    return date.toLocaleDateString("en-GB", {
      day: "numeric",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
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
          <h1 className="text-2xl font-bold text-gray-900">{analysis.job_title}</h1>
          <p className="text-lg text-gray-600">{analysis.company_name}</p>
          <p className="text-sm text-gray-400 mt-1">
            Analyzed on {formatDate(analysis.created_at)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <a
            href={analysis.job_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3 py-2 text-sm text-blue-600 border border-blue-200 rounded-md hover:bg-blue-50"
          >
            <ExternalLink className="w-4 h-4" />
            View Job Post
          </a>
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
        {/* Eligibility Status - Show rejection banner if not eligible */}
        {analysis.eligibility_status === "not_eligible" && (
          <div className="bg-red-50 border border-red-300 rounded-lg p-6">
            <div className="flex items-start gap-3">
              <XCircle className="w-6 h-6 text-red-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h2 className="text-lg font-semibold text-red-800 mb-2">
                  Job Not Eligible
                </h2>
                <p className="text-red-700 mb-4">
                  This job doesn&apos;t meet your requirements. Here&apos;s why:
                </p>
                <ul className="space-y-2">
                  {analysis.eligibility_reasons.map((reason, i) => (
                    <li
                      key={i}
                      className={`flex items-start gap-2 ${
                        reason.startsWith("FAIL")
                          ? "text-red-700"
                          : "text-green-700"
                      }`}
                    >
                      {reason.startsWith("FAIL") ? (
                        <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      ) : (
                        <Check className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      )}
                      <span>{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <p className="text-sm text-gray-500 mt-4">
              Processed in {(analysis.processing_time_ms / 1000).toFixed(1)}s
            </p>
          </div>
        )}

        {/* Partially Eligible Warning */}
        {analysis.eligibility_status === "partially_eligible" && (
          <div className="bg-yellow-50 border border-yellow-300 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="font-medium text-yellow-800">Partially Eligible</h3>
                <ul className="mt-2 space-y-1 text-sm text-yellow-700">
                  {analysis.eligibility_reasons.map((reason, i) => (
                    <li key={i}>{reason}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Matching Score - Only show if not rejected */}
        {analysis.eligibility_status !== "not_eligible" && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Match Score</h2>
              <span className="text-sm text-gray-500">
                Processed in {(analysis.processing_time_ms / 1000).toFixed(1)}s
              </span>
            </div>
            <div className="flex items-center gap-4">
              <div
                className={`text-4xl font-bold px-6 py-3 rounded-lg border ${getScoreColor(analysis.matching_score)}`}
              >
                {analysis.matching_score}%
              </div>
              <p className="text-gray-600 flex-1">{analysis.matching_explanation}</p>
            </div>
          </div>
        )}

        {/* Only show detailed analysis if not rejected */}
        {analysis.eligibility_status !== "not_eligible" && (
          <>
            {/* Job Summary */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-lg font-semibold mb-4">Job Summary</h2>
              <div className="space-y-2">
                <p>
                  <span className="font-medium">Title:</span> {analysis.job_title}
                </p>
                <p>
                  <span className="font-medium">Company:</span> {analysis.company_name}
                </p>
                <div>
                  <span className="font-medium">Key Requirements:</span>
                  <ul className="list-disc list-inside mt-1 text-gray-600">
                    {analysis.key_requirements.map((req, i) => (
                      <li key={i}>{req}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Resume Suggestions */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">
                  Resume Suggestions
                  {analysis.resume_suggestions.length > 0 && (
                    <span className="ml-2 text-sm font-normal text-gray-500">
                      ({analysis.resume_suggestions.length} suggestions in{" "}
                      {Object.keys(groupedSuggestions).length} sections)
                    </span>
                  )}
                </h2>
                {Object.keys(groupedSuggestions).length > 0 && (
                  <div className="flex gap-2">
                    <button
                      onClick={expandAllSections}
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      Expand all
                    </button>
                    <span className="text-gray-300">|</span>
                    <button
                      onClick={collapseAllSections}
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      Collapse all
                    </button>
                  </div>
                )}
              </div>
              <div className="space-y-2">
                {Object.entries(groupedSuggestions).map(([section, suggestions]) => (
                  <div
                    key={section}
                    className="border border-gray-200 rounded-lg overflow-hidden"
                  >
                    <button
                      onClick={() => toggleSection(section)}
                      className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        {expandedSections.has(section) ? (
                          <ChevronDown className="w-4 h-4 text-gray-500" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-gray-500" />
                        )}
                        <span className="font-medium text-gray-800">{section}</span>
                        <span className="text-sm text-gray-500 bg-gray-200 px-2 py-0.5 rounded-full">
                          {suggestions.length}
                        </span>
                      </div>
                    </button>
                    {expandedSections.has(section) && (
                      <div className="px-4 py-3 space-y-3 border-t border-gray-200">
                        {suggestions.map((suggestion, i) => (
                          <div key={i} className="border-l-4 border-blue-500 pl-4">
                            <p className="text-gray-800">{suggestion.suggestion}</p>
                            <p className="text-sm text-gray-500 mt-1">
                              {suggestion.reason}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                {analysis.resume_suggestions.length === 0 && (
                  <p className="text-gray-500">
                    No suggestions - your resume looks good for this role!
                  </p>
                )}
              </div>
            </div>

            {/* ATS Keywords */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h2 className="text-lg font-semibold mb-4">ATS Keywords</h2>
              <div className="flex flex-wrap gap-2">
                {analysis.ats_keywords.map((keyword, i) => (
                  <span
                    key={i}
                    className={`px-3 py-1 rounded-full text-sm flex items-center gap-2 ${
                      keyword.found_in_resume
                        ? "bg-green-100 text-green-700"
                        : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {keyword.found_in_resume && <Check className="w-3 h-3" />}
                    {keyword.keyword}
                    <span
                      className={`text-xs px-1.5 py-0.5 rounded ${getImportanceColor(keyword.importance)}`}
                    >
                      {keyword.importance}
                    </span>
                  </span>
                ))}
              </div>
              <div className="mt-4 text-sm text-gray-500">
                <Check className="w-4 h-4 inline mr-1 text-green-600" />
                = Found in your resume
              </div>
            </div>

            {/* Cover Letter */}
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Generated Cover Letter</h2>
                <button
                  onClick={copyToClipboard}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  {copied ? (
                    <>
                      <Check className="w-4 h-4 text-green-600" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4" />
                      Copy
                    </>
                  )}
                </button>
              </div>
              <div className="bg-gray-50 rounded-lg p-4 whitespace-pre-wrap font-serif text-gray-800 leading-relaxed">
                {analysis.cover_letter}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
