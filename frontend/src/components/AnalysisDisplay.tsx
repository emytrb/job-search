"use client"

import { useState, useMemo } from "react"
import { SavedAnalysis } from "@/lib/api/client"
import { getScoreColor, getImportanceColor } from "@/lib/utils"
import {
  Copy,
  Check,
  XCircle,
  AlertTriangle,
  ChevronDown,
  ChevronRight,
} from "lucide-react"

interface AnalysisDisplayProps {
  analysis: SavedAnalysis
}

export default function AnalysisDisplay({ analysis }: AnalysisDisplayProps) {
  const [copied, setCopied] = useState(false)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set())

  const groupedSuggestions = useMemo(() => {
    if (!analysis.resume_suggestions) return {}
    return analysis.resume_suggestions.reduce(
      (acc, suggestion) => {
        const section = suggestion.section
        if (!acc[section]) {
          acc[section] = []
        }
        acc[section].push(suggestion)
        return acc
      },
      {} as Record<string, typeof analysis.resume_suggestions>
    )
  }, [analysis.resume_suggestions])

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

  function copyToClipboard() {
    if (analysis.cover_letter) {
      navigator.clipboard.writeText(analysis.cover_letter)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
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
          {analysis.key_requirements && analysis.key_requirements.length > 0 && (
            <div>
              <span className="font-medium">Key Requirements:</span>
              <ul className="list-disc list-inside mt-1 text-gray-600">
                {analysis.key_requirements.map((req, i) => (
                  <li key={i}>{req}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Eligibility Status */}
      <div
        className={`rounded-lg border p-6 ${
          analysis.eligibility_status === "not_eligible"
            ? "bg-red-50 border-red-300"
            : analysis.eligibility_status === "partially_eligible"
              ? "bg-yellow-50 border-yellow-300"
              : "bg-green-50 border-green-300"
        }`}
      >
        <div className="flex items-start gap-3">
          {analysis.eligibility_status === "not_eligible" ? (
            <XCircle className="w-6 h-6 text-red-600 mt-0.5 flex-shrink-0" />
          ) : analysis.eligibility_status === "partially_eligible" ? (
            <AlertTriangle className="w-6 h-6 text-yellow-600 mt-0.5 flex-shrink-0" />
          ) : (
            <Check className="w-6 h-6 text-green-600 mt-0.5 flex-shrink-0" />
          )}
          <div className="flex-1">
            <h2
              className={`text-lg font-semibold mb-2 ${
                analysis.eligibility_status === "not_eligible"
                  ? "text-red-800"
                  : analysis.eligibility_status === "partially_eligible"
                    ? "text-yellow-800"
                    : "text-green-800"
              }`}
            >
              {analysis.eligibility_status === "not_eligible"
                ? "Not Eligible"
                : analysis.eligibility_status === "partially_eligible"
                  ? "Partially Eligible"
                  : "Eligible"}
            </h2>
            <ul className="space-y-2">
              {analysis.eligibility_reasons.length > 0 ? (
                analysis.eligibility_reasons.map((reason, i) => (
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
                ))
              ) : (
                <li className="text-gray-500">No eligibility details available. Try requeuing this job for re-analysis.</li>
              )}
            </ul>
          </div>
        </div>
      </div>

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
            <div
              className="bg-gray-50 rounded-lg p-4 whitespace-pre-wrap font-serif text-gray-800 leading-relaxed"
              dangerouslySetInnerHTML={{
                __html: analysis.cover_letter
                  .replace(/&/g, "&amp;")
                  .replace(/</g, "&lt;")
                  .replace(/>/g, "&gt;")
                  .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>"),
              }}
            />
          </div>
        </>
      )}
    </>
  )
}
