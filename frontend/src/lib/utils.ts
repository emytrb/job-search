import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  })
}

export function formatDateTime(dateString: string): string {
  return new Date(dateString).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  })
}

export function getScoreColor(score: number): string {
  if (score >= 80) return "text-green-600 bg-green-50 border-green-200"
  if (score >= 60) return "text-yellow-600 bg-yellow-50 border-yellow-200"
  return "text-red-600 bg-red-50 border-red-200"
}

export function getScoreBadgeColor(score: number): string {
  if (score >= 80) return "text-green-700 bg-green-100"
  if (score >= 60) return "text-yellow-700 bg-yellow-100"
  return "text-red-700 bg-red-100"
}

export function getScoreCardStyle(score: number): string {
  if (score >= 80) return "bg-green-50 border-green-300 hover:border-green-400"
  if (score >= 60) return "bg-yellow-50 border-yellow-300 hover:border-yellow-400"
  return "bg-red-50 border-red-300 hover:border-red-400"
}

export function getImportanceColor(importance: string): string {
  switch (importance.toLowerCase()) {
    case "required":
      return "bg-red-100 text-red-700"
    case "preferred":
      return "bg-yellow-100 text-yellow-700"
    default:
      return "bg-gray-100 text-gray-700"
  }
}
