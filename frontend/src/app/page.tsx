"use client"

import { useState, useEffect, useCallback } from "react"
import Link from "next/link"
import { api, UserPreferences, QueueItem, DuplicateCheckResponse } from "@/lib/api/client"
import {
  Search,
  AlertCircle,
  Loader2,
  XCircle,
  ListOrdered,
  X,
  RefreshCw,
  AlertTriangle,
  Eye,
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
  const [jobTitle, setJobTitle] = useState("")
  const [companyName, setCompanyName] = useState("")
  const [jobText, setJobText] = useState("")
  const [jobUrl, setJobUrl] = useState("")
  const [preferences, setPreferences] = useState<UserPreferences | null>(null)
  const [loadingPrefs, setLoadingPrefs] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [duplicateCheck, setDuplicateCheck] = useState<DuplicateCheckResponse | null>(null)
  const [checkingDuplicate, setCheckingDuplicate] = useState(false)

  // Queue state from backend
  const [queue, setQueue] = useState<QueueItem[]>([])
  const [pendingCount, setPendingCount] = useState(0)
  const [processingCount, setProcessingCount] = useState(0)

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

  // Clear duplicate warning when text changes
  useEffect(() => {
    setDuplicateCheck(null)
  }, [jobText])

  const hasCV = preferences?.cv_text && preferences.cv_text.trim().length > 0
  const isUrlValid = isValidUrl(jobUrl.trim())
  const canAnalyze = hasCV && jobTitle.trim().length > 0 && companyName.trim().length > 0 && jobText.trim().length >= 100 && isUrlValid

  async function submitToQueue() {
    setSubmitting(true)
    setSubmitError(null)

    try {
      await api.analyzer.addToQueue({ job_title: jobTitle.trim(), company_name: companyName.trim(), job_text: jobText, job_url: jobUrl.trim() })
      setJobTitle("")
      setCompanyName("")
      setJobText("")
      setJobUrl("")
      setDuplicateCheck(null)
      await loadQueue()
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

  async function handleAnalyze() {
    if (!canAnalyze) return

    // If user already saw duplicate warning and clicked "Analyze Anyway"
    if (duplicateCheck?.is_duplicate) {
      setDuplicateCheck(null)
      await submitToQueue()
      return
    }

    setCheckingDuplicate(true)
    setSubmitError(null)

    try {
      const result = await api.analyzer.checkDuplicate(jobText)
      if (result.is_duplicate) {
        setDuplicateCheck(result)
        setCheckingDuplicate(false)
        return
      }
      // No duplicate — submit directly
      setCheckingDuplicate(false)
      await submitToQueue()
    } catch {
      // Fail-open: if duplicate check fails, submit anyway
      setCheckingDuplicate(false)
      await submitToQueue()
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

  async function handleRetryQueueItem(id: number) {
    try {
      await api.analyzer.retryQueueItem(id)
      await loadQueue()
    } catch {
      // Silently fail
    }
  }

  if (loadingPrefs) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    )
  }

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

      {duplicateCheck?.is_duplicate && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-amber-800 font-medium">Similar job already analyzed</p>
            <p className="text-amber-700 text-sm">
              <span className="font-medium">{duplicateCheck.matched_job_title}</span>
              {duplicateCheck.matched_company_name && (
                <> at <span className="font-medium">{duplicateCheck.matched_company_name}</span></>
              )}
              {" "}&mdash; {duplicateCheck.similarity_score}% similar
            </p>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Job Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g. Senior Software Engineer"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Company <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-blue-500 focus:border-blue-500"
              placeholder="e.g. Acme Inc."
            />
          </div>
        </div>

        <label className="block text-sm font-medium text-gray-700 mb-2">
          Job Posting Text <span className="text-red-500">*</span>
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
          Job Posting URL <span className="text-red-500">*</span>
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

        <div className="flex items-center justify-end gap-3 mt-4">
          {duplicateCheck?.is_duplicate ? (
            <>
              <Link
                href={`/analyzed-jobs/${duplicateCheck.matched_analysis_id}`}
                className="border border-gray-300 text-gray-700 px-6 py-2 rounded-md hover:bg-gray-50 flex items-center gap-2"
              >
                <Eye className="w-4 h-4" />
                View Job
              </Link>
              <button
                onClick={handleAnalyze}
                disabled={submitting}
                className="bg-amber-500 text-white px-6 py-2 rounded-md hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Adding...
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-4 h-4" />
                    Analyze Anyway
                  </>
                )}
              </button>
            </>
          ) : (
            <button
              onClick={handleAnalyze}
              disabled={!canAnalyze || submitting || checkingDuplicate}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {checkingDuplicate ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Checking...
                </>
              ) : submitting ? (
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
          )}
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
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {item.job_title} - {item.company_name}
                    </p>
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
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-2">
                  {item.status === "failed" && (
                    <button
                      onClick={() => handleRetryQueueItem(item.id)}
                      className="p-1 text-gray-400 hover:text-blue-600 transition-colors"
                      title="Retry"
                    >
                      <RefreshCw className="w-4 h-4" />
                    </button>
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
    </div>
  )
}
