"use client"

import { useEffect, useState } from "react"
import { api, UserPreferences } from "@/lib/api/client"
import { Save, Settings } from "lucide-react"

export default function SettingsPage() {
  const [preferences, setPreferences] = useState<UserPreferences | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    cv_text: "",
    target_stack: "",
    target_seniority: "mid",
    target_location: "London, UK",
    digest_enabled: true,
    digest_hour_utc: 8,
    digest_email: "",
    ats_guidelines: "",
    job_requirements_context: "",
    cover_letter_guidelines: "",
    similarity_threshold: 90,
    sponsorship_bonus_threshold: 50,
    stale_task_timeout_minutes: 10,
  })

  useEffect(() => {
    loadPreferences()
  }, [])

  async function loadPreferences() {
    try {
      setLoading(true)
      const data = await api.preferences.get()
      setPreferences(data)
      setFormData({
        cv_text: data.cv_text || "",
        target_stack: data.target_stack.join(", "),
        target_seniority: data.target_seniority,
        target_location: data.target_location,
        digest_enabled: data.digest_enabled,
        digest_hour_utc: data.digest_hour_utc,
        digest_email: data.digest_email || "",
        ats_guidelines: data.ats_guidelines || "",
        job_requirements_context: data.job_requirements_context || "",
        cover_letter_guidelines: data.cover_letter_guidelines || "",
        similarity_threshold: data.similarity_threshold ?? 90,
        sponsorship_bonus_threshold: data.sponsorship_bonus_threshold ?? 50,
        stale_task_timeout_minutes: data.stale_task_timeout_minutes ?? 10,
      })
    } catch {
      setError("Failed to load preferences")
    } finally {
      setLoading(false)
    }
  }

  async function savePreferences(e: React.FormEvent) {
    e.preventDefault()
    try {
      setSaving(true)
      setError(null)

      await api.preferences.update({
        cv_text: formData.cv_text,
        target_stack: formData.target_stack.split(",").map((s) => s.trim()).filter(Boolean),
        target_seniority: formData.target_seniority,
        target_location: formData.target_location,
        digest_enabled: formData.digest_enabled,
        digest_hour_utc: formData.digest_hour_utc,
        digest_email: formData.digest_email || null,
        ats_guidelines: formData.ats_guidelines,
        job_requirements_context: formData.job_requirements_context,
        cover_letter_guidelines: formData.cover_letter_guidelines,
        similarity_threshold: formData.similarity_threshold,
        sponsorship_bonus_threshold: formData.sponsorship_bonus_threshold,
        stale_task_timeout_minutes: formData.stale_task_timeout_minutes,
      } as Partial<UserPreferences>)

      setSuccess("Preferences saved successfully!")
      setTimeout(() => setSuccess(null), 5000)
    } catch {
      setError("Failed to save preferences")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Settings className="w-8 h-8 text-gray-600" />
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-4">
          {success}
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-500">Loading...</div>
      ) : (
        <form onSubmit={savePreferences} className="space-y-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">Job Matching</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Target Stack
                </label>
                <input
                  type="text"
                  value={formData.target_stack}
                  onChange={(e) => setFormData({ ...formData, target_stack: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                  placeholder="Python, TypeScript, React, PostgreSQL"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Comma-separated list of technologies you're looking for
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Target Seniority
                </label>
                <select
                  value={formData.target_seniority}
                  onChange={(e) => setFormData({ ...formData, target_seniority: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                >
                  <option value="junior">Junior</option>
                  <option value="mid">Mid-level</option>
                  <option value="senior">Senior</option>
                  <option value="staff">Staff</option>
                  <option value="principal">Principal</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Target Location
                </label>
                <input
                  type="text"
                  value={formData.target_location}
                  onChange={(e) => setFormData({ ...formData, target_location: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                  placeholder="London, UK"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CV / Resume Text
                </label>
                <textarea
                  value={formData.cv_text}
                  onChange={(e) => setFormData({ ...formData, cv_text: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 h-40"
                  placeholder="Paste your CV text here for better matching..."
                />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">Email Digest</h2>

            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="digest_enabled"
                  checked={formData.digest_enabled}
                  onChange={(e) => setFormData({ ...formData, digest_enabled: e.target.checked })}
                  className="h-4 w-4 text-blue-600 rounded"
                />
                <label htmlFor="digest_enabled" className="text-sm font-medium text-gray-700">
                  Enable daily email digest
                </label>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Digest Email
                </label>
                <input
                  type="email"
                  value={formData.digest_email}
                  onChange={(e) => setFormData({ ...formData, digest_email: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                  placeholder="your@email.com"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Leave empty to use the default email from environment
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Digest Hour (UTC)
                </label>
                <select
                  value={formData.digest_hour_utc}
                  onChange={(e) => setFormData({ ...formData, digest_hour_utc: parseInt(e.target.value) })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                >
                  {Array.from({ length: 24 }, (_, i) => (
                    <option key={i} value={i}>
                      {i.toString().padStart(2, "0")}:00 UTC
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold mb-4">Analyzer Guidelines</h2>
            <p className="text-sm text-gray-600 mb-4">
              Customize how the Job Analyzer processes job postings and generates recommendations.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Job Requirements Context
                </label>
                <textarea
                  value={formData.job_requirements_context}
                  onChange={(e) => setFormData({ ...formData, job_requirements_context: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 h-24"
                  placeholder="I have 4 years experience. I need visa sponsorship. Looking for remote-friendly roles."
                />
                <p className="text-xs text-gray-500 mt-1">
                  Context about your situation that helps the AI understand your needs better.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  ATS Guidelines
                </label>
                <textarea
                  value={formData.ats_guidelines}
                  onChange={(e) => setFormData({ ...formData, ats_guidelines: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 h-24"
                  placeholder="Focus on keywords from job title. Prioritize exact matches over synonyms."
                />
                <p className="text-xs text-gray-500 mt-1">
                  Custom rules for how ATS keywords should be analyzed.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cover Letter Guidelines
                </label>
                <textarea
                  value={formData.cover_letter_guidelines}
                  onChange={(e) => setFormData({ ...formData, cover_letter_guidelines: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 h-24"
                  placeholder="Keep formal tone. Mention my open source contributions. Always include a specific company detail."
                />
                <p className="text-xs text-gray-500 mt-1">
                  Style preferences for generated cover letters.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Duplicate Detection Threshold: {formData.similarity_threshold}%
                </label>
                <input
                  type="range"
                  min={50}
                  max={100}
                  value={formData.similarity_threshold}
                  onChange={(e) => setFormData({ ...formData, similarity_threshold: parseInt(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>50% (loose)</span>
                  <span>100% (disabled)</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  How similar a job must be to trigger a duplicate warning. Set to 100% to effectively disable duplicate detection.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Sponsorship Bonus Threshold: {formData.sponsorship_bonus_threshold}%
                </label>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={formData.sponsorship_bonus_threshold}
                  onChange={(e) => setFormData({ ...formData, sponsorship_bonus_threshold: parseInt(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>0% (always apply)</span>
                  <span>100% (disable)</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Minimum match score required to apply the +20% sponsorship bonus. Set to 100% to disable.
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Stale Task Timeout: {formData.stale_task_timeout_minutes} minutes
                </label>
                <input
                  type="range"
                  min={5}
                  max={30}
                  step={1}
                  value={formData.stale_task_timeout_minutes}
                  onChange={(e) => setFormData({ ...formData, stale_task_timeout_minutes: parseInt(e.target.value) })}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                />
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>5 min (aggressive)</span>
                  <span>30 min (conservative)</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  How long a task can stay processing before being automatically reset. Increase if your analyses are slow due to rate limits.
                </p>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
            >
              <Save className="w-4 h-4" />
              {saving ? "Saving..." : "Save Preferences"}
            </button>
          </div>
        </form>
      )}
    </div>
  )
}
