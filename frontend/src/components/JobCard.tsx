"use client"

import { Job, JobScore } from "@/lib/api/client"
import { formatDate, formatSalary, getScoreColor } from "@/lib/utils"
import { MapPin, Building2, Calendar, ExternalLink } from "lucide-react"

interface JobCardProps {
  job: Job
  score?: JobScore | null
  onClick?: () => void
}

export function JobCard({ job, score, onClick }: JobCardProps) {
  const salary = formatSalary(job.salary_min, job.salary_max, job.salary_currency)

  return (
    <div
      className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
      onClick={onClick}
    >
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 hover:text-blue-600">
            {job.title}
          </h3>
          <div className="flex items-center gap-2 mt-1 text-gray-600">
            <Building2 className="w-4 h-4" />
            <span>{job.company_name}</span>
          </div>
          {job.location && (
            <div className="flex items-center gap-2 mt-1 text-gray-500 text-sm">
              <MapPin className="w-4 h-4" />
              <span>{job.location}</span>
            </div>
          )}
          <div className="flex items-center gap-2 mt-1 text-gray-400 text-sm">
            <Calendar className="w-4 h-4" />
            <span>{formatDate(job.created_at)}</span>
          </div>
        </div>

        <div className="flex flex-col items-end gap-2">
          {score && (
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(score.total_score)}`}>
              {score.total_score.toFixed(0)}
            </span>
          )}
          {salary && (
            <span className="text-sm text-gray-600 font-medium">
              {salary}
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 mt-3">
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
          job.status === "scored" ? "bg-green-100 text-green-700" :
          job.status === "applied" ? "bg-blue-100 text-blue-700" :
          job.status === "dismissed" ? "bg-gray-100 text-gray-700" :
          "bg-yellow-100 text-yellow-700"
        }`}>
          {job.status}
        </span>

        {job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 text-sm flex items-center gap-1"
            onClick={(e) => e.stopPropagation()}
          >
            <ExternalLink className="w-3 h-3" />
            Apply
          </a>
        )}
      </div>
    </div>
  )
}
