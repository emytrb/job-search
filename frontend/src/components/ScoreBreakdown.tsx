"use client"

import { JobScore } from "@/lib/api/client"

interface ScoreBreakdownProps {
  score: JobScore
}

export function ScoreBreakdown({ score }: ScoreBreakdownProps) {
  const scores = [
    { label: "Stack Match", value: score.stack_match_score, weight: 35, color: "bg-blue-500" },
    { label: "Seniority", value: score.seniority_match_score, weight: 25, color: "bg-purple-500" },
    { label: "Sponsorship", value: score.sponsorship_score, weight: 25, color: "bg-green-500" },
    { label: "Quality", value: score.quality_score, weight: 15, color: "bg-orange-500" },
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Score Breakdown</h3>
        <span className="text-2xl font-bold text-blue-600">{score.total_score.toFixed(1)}</span>
      </div>

      <div className="space-y-3">
        {scores.map((item) => (
          <div key={item.label}>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-600">{item.label}</span>
              <span className="font-medium">{item.value.toFixed(1)} ({item.weight}%)</span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full ${item.color} rounded-full transition-all`}
                style={{ width: `${item.value}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {score.stack_match_details > 0 && (
        <p className="text-sm text-gray-500">
          Matched {score.stack_match_details} technologies from your target stack
        </p>
      )}
    </div>
  )
}
