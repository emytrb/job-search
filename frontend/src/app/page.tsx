"use client"

import { useState, useEffect, useMemo, useCallback } from "react"
import Link from "next/link"
import { api, SavedAnalysis, UserPreferences, QueueItem } from "@/lib/api/client"
import {
  Search,
  Copy,
  Check,
  AlertCircle,
  Loader2,
  XCircle,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
  ListOrdered,
  X,
  RefreshCw,
} from "lucide-react"

function isValidUrl(url: string): boolean {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

export default function AnalyzerPage() {
  const [jobText, setJobText] = useState("")
  const [jobUrl, setJobUrl] = useState("")
  const [preferences, setPreferences] = useState<UserPreferences | null>(null)
  const [loadingPrefs, setLoadingPrefs] = useState(true)
  const [copied, setCopied] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set())
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  // Queue state from backend
  const [queue, setQueue] = useState<QueueItem[]>([])
  const [pendingCount, setPendingCount] = useState(0)
  const [processingCount, setProcessingCount] = useState(0)

  // Selected result to display
  const [selectedAnalysis, setSelectedAnalysis] = useState<SavedAnalysis | null>(null)
  const [loadingAnalysis, setLoadingAnalysis] = useState(false)

  useEffect(() => {
    loadPreferences()
    loadQueue()
  }, [])

  // Poll queue status when there are pending or processing items
  useEffect(() => {
    if (pendingCount > 0 || processingCount > 0) {
      const interval = setInterval(loadQueue, 3000) // Poll every 3 seconds
      return () => clearInterval(interval)
    }
  }, [pendingCount, processingCount])

  async function loadPreferences() {
    try {
      const prefs = await api.preferences.get()
      setPreferences(prefs)
    } catch {
      // Error handled silently, user will see CV warning
    } finally {
      setLoadingPrefs(false)
    }
  }

  const loadQueue = useCallback(async () => {
    try {
      const response = await api.analyzer.getQueue()
      setQueue(response.items)
      setPendingCount(response.pending_count)
      setProcessingCount(response.processing_count)
    } catch {
      // Silently fail, will retry on next poll
    }
  }, [])

  const hasCV = preferences?.cv_text && preferences.cv_text.trim().length > 0
  const isUrlValid = isValidUrl(jobUrl.trim())
  const canAnalyze = hasCV && jobText.trim().length >= 100 && isUrlValid

  async function handleAnalyze() {
    if (!canAnalyze) return

    setSubmitting(true)
    setSubmitError(null)

    try {
      await api.analyzer.addToQueue({ job_text: jobText, job_url: jobUrl.trim() })
      setJobText("") // Clear input after adding to queue
      setJobUrl("") // Clear URL after adding to queue
      await loadQueue() // Refresh queue immediately
    } catch (err) {
      if (err instanceof Error) {
        setSubmitError(err.message)
      } else {
        setSubmitError("Failed to add to queue")
      }
    } finally {
      setSubmitting(false)
    }
  }

  async function handleRemoveFromQueue(id: number) {
    try {
      await api.analyzer.removeFromQueue(id)
      setQueue((prev) => prev.filter((item) => item.id !== id))
    } catch {
      // Silently fail
    }
  }

  async function handleViewResult(item: QueueItem) {
    if (!item.saved_analysis_id) return

    setLoadingAnalysis(true)
    try {
      const analysis = await api.analyzer.get(item.saved_analysis_id)
      setSelectedAnalysis(analysis)
    } catch {
      // Silently fail
    } finally {
      setLoadingAnalysis(false)
    }
  }

  function copyToClipboard() {
    if (selectedAnalysis?.cover_letter) {
      navigator.clipboard.writeText(selectedAnalysis.cover_letter)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
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
    if (!selectedAnalysis?.resume_suggestions) return {}
    return selectedAnalysis.resume_suggestions.reduce(
      (acc, suggestion) => {
        const section = suggestion.section
        if (!acc[section]) {
          acc[section] = []
        }
        acc[section].push(suggestion)
        return acc
      },
      {} as Record<string, typeof selectedAnalysis.resume_suggestions>
    )
  }, [selectedAnalysis?.resume_suggestions])

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

  if (loadingPrefs) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    )
  }

  const result = selectedAnalysis

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Search className="w-8 h-8 text-gray-600" />
        <h1 className="text-2xl font-bold text-gray-900">Job Analyzer</h1>
      </div>

      {!hasCV && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-yellow-800 font-medium">CV Required</p>
            <p className="text-yellow-700 text-sm">
              Please add your CV text in{" "}
              <a href="/settings" className="underline hover:text-yellow-900">
                Settings
              </a>{" "}
              before using the analyzer.
            </p>
          </div>
        </div>
      )}

      {submitError && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {submitError}
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Job Posting Text
        </label>
        <textarea
          value={jobText}
          onChange={(e) => setJobText(e.target.value)}
          className="w-full border border-gray-300 rounded-md px-3 py-2 h-48 font-mono text-sm"
          placeholder="Paste the full job description here..."
        />
        <p className="text-xs text-gray-500 mt-1">
          {jobText.length} characters {jobText.length < 100 && "(minimum 100)"}
        </p>

        <label className="block text-sm font-medium text-gray-700 mb-2 mt-4">
          Job Posting URL
        </label>
        <input
          type="url"
          value={jobUrl}
          onChange={(e) => setJobUrl(e.target.value)}
          className={`w-full border rounded-md px-3 py-2 text-sm ${
            jobUrl && !isUrlValid
              ? "border-red-300 focus:ring-red-500 focus:border-red-500"
              : "border-gray-300 focus:ring-blue-500 focus:border-blue-500"
          }`}
          placeholder="https://example.com/jobs/123"
        />
        {jobUrl && !isUrlValid && (
          <p className="text-xs text-red-500 mt-1">Please enter a valid URL</p>
        )}

        <div className="flex items-center justify-end mt-4">
          <button
            onClick={handleAnalyze}
            disabled={!canAnalyze || submitting}
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Adding...
              </>
            ) : processingCount > 0 ? (
              <>
                <ListOrdered className="w-4 h-4" />
                Add to Queue
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                Analyze
              </>
            )}
          </button>
        </div>
      </div>

      {/* Queue Status */}
      {queue.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <ListOrdered className="w-5 h-5 text-gray-600" />
              <h3 className="font-semibold text-gray-900">Analysis Queue</h3>
              <span className="text-sm text-gray-500">
                ({queue.length} item{queue.length !== 1 ? "s" : ""})
              </span>
            </div>
            <button
              onClick={loadQueue}
              className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
              title="Refresh queue"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
          <div className="space-y-2">
            {queue.map((item, index) => (
              <div
                key={item.id}
                className={`flex items-center justify-between p-3 rounded-lg border ${
                  item.status === "processing"
                    ? "bg-blue-50 border-blue-200"
                    : item.status === "completed"
                      ? "bg-green-50 border-green-200"
                      : item.status === "failed"
                        ? "bg-red-50 border-red-200"
                        : "bg-gray-50 border-gray-200"
                }`}
              >
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <span className="text-sm font-medium text-gray-500 w-6">
                    #{index + 1}
                  </span>
                  {item.status === "processing" && (
                    <Loader2 className="w-4 h-4 animate-spin text-blue-600 flex-shrink-0" />
                  )}
                  {item.status === "completed" && (
                    <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                  )}
                  {item.status === "failed" && (
                    <XCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
                  )}
                  {item.status === "pending" && item.retry_count > 0 && (
                    <RefreshCw className="w-4 h-4 text-orange-500 flex-shrink-0" />
                  )}
                  {item.status === "pending" && item.retry_count === 0 && (
                    <div className="w-4 h-4 rounded-full border-2 border-gray-300 flex-shrink-0" />
                  )}
                  <div className="min-w-0 flex-1">
                    {item.job_title ? (
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {item.job_title} - {item.company_name}
                      </p>
                    ) : (
                      <p className="text-sm text-gray-600 truncate">
                        {item.job_text_preview}
                      </p>
                    )}
                    {item.status === "processing" && (
                      <p className="text-xs text-blue-600">Analyzing...</p>
                    )}
                    {item.status === "pending" && item.retry_count > 0 && (
                      <p className="text-xs text-orange-600">
                        Retry {item.retry_count}/{item.max_retries} pending...
                      </p>
                    )}
                    {item.status === "failed" && (
                      <p className="text-xs text-red-600">
                        {item.error_message}
                        {item.retry_count >= item.max_retries && (
                          <span className="ml-1 text-gray-500">
                            (after {item.retry_count} retries)
                          </span>
                        )}
                      </p>
                    )}
                    {item.status === "completed" && item.matching_score !== null && (
                      <p className="text-xs text-green-600">
                        Score: {item.matching_score}%
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-2">
                  {item.status === "completed" && item.saved_analysis_id && (
                    <>
                      <button
                        onClick={() => handleViewResult(item)}
                        className="text-xs text-blue-600 hover:text-blue-800 px-2 py-1 rounded hover:bg-blue-50"
                      >
                        View
                      </button>
                      <Link
                        href={`/analyzed-jobs/${item.saved_analysis_id}`}
                        className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1 rounded hover:bg-gray-100"
                      >
                        Open
                      </Link>
                    </>
                  )}
                  {item.status !== "processing" && (
                    <button
                      onClick={() => handleRemoveFromQueue(item.id)}
                      className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                      title="Remove"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
          {pendingCount > 0 && processingCount > 0 && (
            <p className="text-xs text-gray-500 mt-2">
              {pendingCount} job{pendingCount !== 1 ? "s" : ""} waiting in queue
            </p>
          )}
        </div>
      )}

      {loadingAnalysis && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center mb-6">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-3" />
          <p className="text-blue-800 font-medium">Loading analysis...</p>
        </div>
      )}

      {result && (
        <div className="space-y-6">
          {/* Saved confirmation banner */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Check className="w-5 h-5 text-green-600" />
              <span className="text-green-800">
                Viewing analysis for <strong>{result.job_title}</strong> at{" "}
                <strong>{result.company_name}</strong>
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Link
                href={`/analyzed-jobs/${result.id}`}
                className="text-sm text-green-700 hover:text-green-900 underline"
              >
                Open full page
              </Link>
              <button
                onClick={() => setSelectedAnalysis(null)}
                className="text-sm text-gray-500 hover:text-gray-700 ml-2"
              >
                Close
              </button>
            </div>
          </div>

          {/* Job Summary - Always shown at the top */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">Job Summary</h2>
            <div className="space-y-2">
              <p>
                <span className="font-medium">Title:</span> {result.job_title}
              </p>
              <p>
                <span className="font-medium">Company:</span> {result.company_name}
              </p>
              {result.key_requirements && result.key_requirements.length > 0 && (
                <div>
                  <span className="font-medium">Key Requirements:</span>
                  <ul className="list-disc list-inside mt-1 text-gray-600">
                    {result.key_requirements.map((req, i) => (
                      <li key={i}>{req}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Eligibility Status - Show rejection banner if not eligible */}
          {result.eligibility_status === "not_eligible" && (
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
                    {result.eligibility_reasons.map((reason, i) => (
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
                Processed in {(result.processing_time_ms / 1000).toFixed(1)}s
              </p>
            </div>
          )}

          {/* Partially Eligible Warning */}
          {result.eligibility_status === "partially_eligible" && (
            <div className="bg-yellow-50 border border-yellow-300 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h3 className="font-medium text-yellow-800">Partially Eligible</h3>
                  <ul className="mt-2 space-y-1 text-sm text-yellow-700">
                    {result.eligibility_reasons.map((reason, i) => (
                      <li key={i}>{reason}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* Matching Score - Only show if not rejected */}
          {result.eligibility_status !== "not_eligible" && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Match Score</h2>
                <span className="text-sm text-gray-500">
                  Processed in {(result.processing_time_ms / 1000).toFixed(1)}s
                </span>
              </div>
              <div className="flex items-center gap-4">
                <div
                  className={`text-4xl font-bold px-6 py-3 rounded-lg border ${getScoreColor(result.matching_score)}`}
                >
                  {result.matching_score}%
                </div>
                <p className="text-gray-600 flex-1">{result.matching_explanation}</p>
              </div>
            </div>
          )}

          {/* Only show detailed analysis if not rejected */}
          {result.eligibility_status !== "not_eligible" && (
            <>
              {/* Resume Suggestions */}
              <div className="bg-white rounded-lg border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">
                    Resume Suggestions
                    {result.resume_suggestions.length > 0 && (
                      <span className="ml-2 text-sm font-normal text-gray-500">
                        ({result.resume_suggestions.length} suggestions in{" "}
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
                  {result.resume_suggestions.length === 0 && (
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
                  {result.ats_keywords.map((keyword, i) => (
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
                  <Check className="w-4 h-4 inline mr-1 text-green-600" />= Found in your
                  resume
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
                  {result.cover_letter}
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
