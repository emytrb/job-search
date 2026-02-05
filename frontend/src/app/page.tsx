"use client"

import { useEffect, useState } from "react"
import { api, Job, JobDetail, JobScore } from "@/lib/api/client"
import { JobCard } from "@/components/JobCard"
import { ScoreBreakdown } from "@/components/ScoreBreakdown"
import { X } from "lucide-react"

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [scores, setScores] = useState<Record<number, JobScore>>({})
  const [selectedJob, setSelectedJob] = useState<JobDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<string>("scored")

  useEffect(() => {
    loadJobs()
  }, [filter])

  async function loadJobs() {
    try {
      setLoading(true)
      const response = await api.jobs.list({ status: filter || undefined, limit: 50 })
      setJobs(response.jobs)

      const scoreMap: Record<number, JobScore> = {}
      for (const job of response.jobs) {
        try {
          const detail = await api.jobs.get(job.id)
          if (detail.score) {
            scoreMap[job.id] = detail.score
          }
        } catch {
          // Skip if we can't get the score
        }
      }
      setScores(scoreMap)
    } catch (e) {
      setError("Failed to load jobs")
    } finally {
      setLoading(false)
    }
  }

  async function openJobDetail(jobId: number) {
    try {
      const detail = await api.jobs.get(jobId)
      setSelectedJob(detail)
    } catch {
      setError("Failed to load job details")
    }
  }

  async function dismissJob(jobId: number) {
    try {
      await api.jobs.dismiss(jobId)
      setSelectedJob(null)
      loadJobs()
    } catch {
      setError("Failed to dismiss job")
    }
  }

  async function markApplied(jobId: number) {
    try {
      await api.jobs.apply(jobId)
      setSelectedJob(null)
      loadJobs()
    } catch {
      setError("Failed to mark as applied")
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-2 text-sm"
        >
          <option value="scored">Scored</option>
          <option value="applied">Applied</option>
          <option value="dismissed">Dismissed</option>
          <option value="filtered_out">Filtered Out</option>
        </select>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-500">Loading...</div>
      ) : jobs.length === 0 ? (
        <div className="text-center py-8 text-gray-500">No jobs found</div>
      ) : (
        <div className="grid gap-4">
          {jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              score={scores[job.id]}
              onClick={() => openJobDetail(job.id)}
            />
          ))}
        </div>
      )}

      {selectedJob && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
              <h2 className="text-xl font-semibold">{selectedJob.job.title}</h2>
              <button
                onClick={() => setSelectedJob(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              <div>
                <p className="text-lg text-gray-700">{selectedJob.job.company_name}</p>
                {selectedJob.job.location && (
                  <p className="text-gray-500">{selectedJob.job.location}</p>
                )}
              </div>

              {selectedJob.score && <ScoreBreakdown score={selectedJob.score} />}

              {selectedJob.analysis && (
                <div className="space-y-3">
                  <h3 className="text-lg font-semibold">Analysis</h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-500">Seniority:</span>
                      <span className="ml-2 font-medium capitalize">
                        {selectedJob.analysis.seniority_level || "Unknown"}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-500">Remote:</span>
                      <span className="ml-2 font-medium capitalize">
                        {selectedJob.analysis.remote_policy || "Unknown"}
                      </span>
                    </div>
                    {selectedJob.analysis.required_experience_years && (
                      <div>
                        <span className="text-gray-500">Experience:</span>
                        <span className="ml-2 font-medium">
                          {selectedJob.analysis.required_experience_years} years
                        </span>
                      </div>
                    )}
                    <div>
                      <span className="text-gray-500">Sponsorship:</span>
                      <span className="ml-2 font-medium">
                        {((selectedJob.analysis.sponsorship_likelihood || 0) * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  {selectedJob.analysis.detected_stack.length > 0 && (
                    <div>
                      <span className="text-gray-500 text-sm">Stack:</span>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {selectedJob.analysis.detected_stack.map((tech) => (
                          <span
                            key={tech}
                            className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs"
                          >
                            {tech}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              <div className="flex gap-3 pt-4 border-t">
                {selectedJob.job.url && (
                  <a
                    href={selectedJob.job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 bg-blue-600 text-white text-center py-2 rounded-md hover:bg-blue-700"
                  >
                    View Job
                  </a>
                )}
                <button
                  onClick={() => markApplied(selectedJob.job.id)}
                  className="flex-1 bg-green-600 text-white py-2 rounded-md hover:bg-green-700"
                >
                  Mark Applied
                </button>
                <button
                  onClick={() => dismissJob(selectedJob.job.id)}
                  className="flex-1 bg-gray-200 text-gray-700 py-2 rounded-md hover:bg-gray-300"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
