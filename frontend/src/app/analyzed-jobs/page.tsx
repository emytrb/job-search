"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { api, SavedAnalysisListItem } from "@/lib/api/client"
import { FileText, Loader2, Trash2, Check, XCircle, AlertTriangle, CheckSquare, Square, RefreshCw, X } from "lucide-react"

export default function AnalyzedJobsPage() {
  const router = useRouter()
  const [analyses, setAnalyses] = useState<SavedAnalysisListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<number | null>(null)
  const [selectMode, setSelectMode] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set())
  const [requeuing, setRequeuing] = useState(false)
  const [appliedFilter, setAppliedFilter] = useState<"not_applied" | "applied" | "both">("not_applied")

  useEffect(() => {
    loadAnalyses()
  }, [appliedFilter])

  async function loadAnalyses() {
    try {
      const appliedParam = appliedFilter === "not_applied" ? false : appliedFilter === "applied" ? true : null
      const response = await api.analyzer.list({ applied: appliedParam })
      setAnalyses(response.analyses)
    } catch {
      setError("Failed to load analyzed jobs")
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(id: number, e: React.MouseEvent) {
    e.preventDefault()
    e.stopPropagation()

    if (!confirm("Are you sure you want to delete this analysis?")) return

    setDeleting(id)
    try {
      await api.analyzer.delete(id)
      setAnalyses(analyses.filter(a => a.id !== id))
    } catch {
      setError("Failed to delete analysis")
    } finally {
      setDeleting(null)
    }
  }

  function getScoreBadgeColor(score: number) {
    if (score >= 80) return "text-green-700 bg-green-100"
    if (score >= 60) return "text-yellow-700 bg-yellow-100"
    return "text-red-700 bg-red-100"
  }

  function getCardStyle(score: number) {
    if (score >= 80) return "bg-green-50 border-green-300 hover:border-green-400"
    if (score >= 60) return "bg-yellow-50 border-yellow-300 hover:border-yellow-400"
    return "bg-red-50 border-red-300 hover:border-red-400"
  }

  function getStatusIcon(status: string) {
    switch (status) {
      case "eligible":
        return <Check className="w-4 h-4 text-green-600" />
      case "partially_eligible":
        return <AlertTriangle className="w-4 h-4 text-yellow-600" />
      case "not_eligible":
        return <XCircle className="w-4 h-4 text-red-600" />
      default:
        return null
    }
  }

  // Sort analyses by matching score (highest first)
  const sortedAnalyses = [...analyses].sort((a, b) => b.matching_score - a.matching_score)

  function toggleSelection(id: number) {
    const newSelected = new Set(selectedIds)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedIds(newSelected)
  }

  function selectAll() {
    setSelectedIds(new Set(analyses.map(a => a.id)))
  }

  function deselectAll() {
    setSelectedIds(new Set())
  }

  function exitSelectMode() {
    setSelectMode(false)
    setSelectedIds(new Set())
  }

  async function handleRequeue() {
    if (selectedIds.size === 0) return

    setRequeuing(true)
    setError(null)
    try {
      await api.analyzer.requeue(Array.from(selectedIds))
      exitSelectMode()
      router.push("")
    } catch {
      setError("Failed to requeue analyses")
    } finally {
      setRequeuing(false)
    }
  }

  function handleCardClick(e: React.MouseEvent, analysisId: number) {
    if (selectMode) {
      e.preventDefault()
      toggleSelection(analysisId)
    }
  }

  function formatDate(dateString: string) {
    const date = new Date(dateString)
    return date.toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
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

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <FileText className="w-8 h-8 text-gray-600" />
          <h1 className="text-2xl font-bold text-gray-900">Analyzed Jobs</h1>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={appliedFilter}
            onChange={(e) => setAppliedFilter(e.target.value as "not_applied" | "applied" | "both")}
            className="text-sm border border-gray-300 rounded-md px-3 py-2 bg-white text-gray-700"
          >
            <option value="not_applied">Not Applied</option>
            <option value="applied">Applied</option>
            <option value="both">All Jobs</option>
          </select>
          {selectMode ? (
            <>
              <button
                onClick={selectAll}
                className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm"
              >
                Select All
              </button>
              <button
                onClick={deselectAll}
                className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm"
              >
                Deselect All
              </button>
              <button
                onClick={handleRequeue}
                disabled={selectedIds.size === 0 || requeuing}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {requeuing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4" />
                )}
                Requeue Selected ({selectedIds.size})
              </button>
              <button
                onClick={exitSelectMode}
                className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm flex items-center gap-1"
              >
                <X className="w-4 h-4" />
                Cancel
              </button>
            </>
          ) : (
            <>
              {analyses.length > 0 && (
                <button
                  onClick={() => setSelectMode(true)}
                  className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm border border-gray-300 rounded-md"
                >
                  Select
                </button>
              )}
              <Link
                href="/analyzer"
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm"
              >
                Analyze New Job
              </Link>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {analyses.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h2 className="text-lg font-medium text-gray-900 mb-2">No analyzed jobs yet</h2>
          <p className="text-gray-500 mb-4">
            Analyze your first job posting to see it here.
          </p>
          <Link
            href="/analyzer"
            className="inline-block bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700"
          >
            Analyze a Job
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sortedAnalyses.map((analysis) => {
            const isSelected = selectedIds.has(analysis.id)
            const CardWrapper = selectMode ? "div" : Link
            const cardProps = selectMode
              ? { onClick: (e: React.MouseEvent) => handleCardClick(e, analysis.id) }
              : { href: `/analyzed-jobs/${analysis.id}` }

            return (
              <CardWrapper
                key={analysis.id}
                {...(cardProps as React.ComponentProps<typeof CardWrapper>)}
                className={`block rounded-lg border-2 p-4 hover:shadow-md transition-all cursor-pointer ${getCardStyle(analysis.matching_score)} ${isSelected ? "ring-2 ring-blue-500 ring-offset-2" : ""}`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {selectMode && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          toggleSelection(analysis.id)
                        }}
                        className="mr-1"
                      >
                        {isSelected ? (
                          <CheckSquare className="w-5 h-5 text-blue-600" />
                        ) : (
                          <Square className="w-5 h-5 text-gray-400" />
                        )}
                      </button>
                    )}
                    <span className={`text-3xl font-bold px-3 py-1 rounded-lg ${getScoreBadgeColor(analysis.matching_score)}`}>
                      {analysis.matching_score}%
                    </span>
                    {getStatusIcon(analysis.eligibility_status)}
                  </div>
                  {!selectMode && (
                    <button
                      onClick={(e) => handleDelete(analysis.id, e)}
                      disabled={deleting === analysis.id}
                      className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                      title="Delete analysis"
                    >
                      {deleting === analysis.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </button>
                  )}
                </div>
                <h3 className="font-semibold text-gray-900 mb-1 line-clamp-2">
                  {analysis.job_title}
                </h3>
                <p className="text-gray-600 text-sm mb-2">{analysis.company_name}</p>
                <div className="flex items-center gap-2">
                  <p className="text-gray-400 text-xs">{formatDate(analysis.last_analyzed_at)}</p>
                  {analysis.applied && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 font-medium">
                      Applied
                    </span>
                  )}
                </div>
              </CardWrapper>
            )
          })}
        </div>
      )}
    </div>
  )
}
