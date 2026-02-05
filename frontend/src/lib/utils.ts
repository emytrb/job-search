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

export function formatSalary(min: number | null, max: number | null, currency: string | null): string {
  if (!min && !max) return ""
  const curr = currency || "GBP"
  const symbol = curr === "GBP" ? "£" : curr === "EUR" ? "€" : "$"

  if (min && max) {
    return `${symbol}${(min / 1000).toFixed(0)}k - ${symbol}${(max / 1000).toFixed(0)}k`
  }
  if (min) {
    return `${symbol}${(min / 1000).toFixed(0)}k+`
  }
  return `Up to ${symbol}${(max! / 1000).toFixed(0)}k`
}

export function getScoreColor(score: number): string {
  if (score >= 70) return "text-green-600 bg-green-100"
  if (score >= 50) return "text-yellow-600 bg-yellow-100"
  return "text-red-600 bg-red-100"
}
