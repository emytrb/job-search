"use client"

import { useEffect, useState } from "react"
import { api, ScrapeSource } from "@/lib/api/client"
import { formatDate } from "@/lib/utils"
import { Plus, Play, Trash2, ExternalLink } from "lucide-react"

export default function SourcesPage() {
  const [sources, setSources] = useState<ScrapeSource[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    name: "",
    source_type: "greenhouse",
    base_url: "",
    risk_level: "low",
  })

  useEffect(() => {
    loadSources()
  }, [])

  async function loadSources() {
    try {
      setLoading(true)
      setError(null)
      console.log("Loading sources...")
      const data = await api.sources.list()
      console.log("Sources loaded:", data)
      setSources(data)
    } catch (err) {
      console.error("Failed to load sources:", err)
      setError(`Failed to load sources: ${err instanceof Error ? err.message : String(err)}`)
    } finally {
      setLoading(false)
    }
  }

  async function createSource(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      console.log("Creating source with data:", formData)
      const result = await api.sources.create(formData)
      console.log("Source created:", result)
      setShowForm(false)
      setFormData({ name: "", source_type: "greenhouse", base_url: "", risk_level: "low" })
      loadSources()
    } catch (err) {
      console.error("Failed to create source:", err)
      setError(`Failed to create source: ${err instanceof Error ? err.message : String(err)}`)
    }
  }

  async function triggerScrape(sourceId: number) {
    try {
      await api.sources.scrape(sourceId)
      alert("Scrape triggered successfully")
    } catch {
      setError("Failed to trigger scrape")
    }
  }

  async function deleteSource(sourceId: number) {
    if (!confirm("Are you sure you want to delete this source?")) return
    try {
      await api.sources.delete(sourceId)
      loadSources()
    } catch {
      setError("Failed to delete source")
    }
  }

  async function toggleEnabled(source: ScrapeSource) {
    try {
      await api.sources.update(source.id, { enabled: !source.enabled })
      loadSources()
    } catch {
      setError("Failed to update source")
    }
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Scrape Sources</h1>
        <button
          onClick={() => setShowForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Add Source
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {showForm && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Add New Source</h2>
          <form onSubmit={createSource} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Source Type</label>
              <select
                value={formData.source_type}
                onChange={(e) => setFormData({ ...formData, source_type: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              >
                <option value="greenhouse">Greenhouse</option>
                <option value="lever">Lever</option>
                <option value="wttj">Welcome to the Jungle</option>
                <option value="indeed">Indeed</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Base URL</label>
              <input
                type="url"
                value={formData.base_url}
                onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                placeholder="https://boards.greenhouse.io/company"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Risk Level</label>
              <select
                value={formData.risk_level}
                onChange={(e) => setFormData({ ...formData, risk_level: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              >
                <option value="low">Low (every 6h)</option>
                <option value="medium">Medium (every 12h)</option>
                <option value="high">High (every 24h)</option>
              </select>
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                Create Source
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-gray-500">Loading...</div>
      ) : sources.length === 0 ? (
        <div className="text-center py-8 text-gray-500">No sources configured</div>
      ) : (
        <div className="grid gap-4">
          {sources.map((source) => (
            <div
              key={source.id}
              className="bg-white rounded-lg border border-gray-200 p-4"
            >
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-semibold text-gray-900">{source.name}</h3>
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                      source.enabled ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"
                    }`}>
                      {source.enabled ? "Enabled" : "Disabled"}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    {source.source_type} - {source.risk_level} risk
                  </p>
                  <a
                    href={source.base_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 hover:underline inline-flex items-center gap-1 mt-1 break-all"
                  >
                    {source.base_url}
                    <ExternalLink className="w-3 h-3 flex-shrink-0" />
                  </a>
                  {source.last_scraped_at && (
                    <p className="text-xs text-gray-400 mt-2">
                      Last scraped: {formatDate(source.last_scraped_at)}
                    </p>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => toggleEnabled(source)}
                    className="text-gray-400 hover:text-gray-600 px-3 py-1 text-sm border rounded"
                  >
                    {source.enabled ? "Disable" : "Enable"}
                  </button>
                  <button
                    onClick={() => triggerScrape(source.id)}
                    className="text-blue-600 hover:text-blue-800 p-2"
                    title="Trigger scrape"
                  >
                    <Play className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => deleteSource(source.id)}
                    className="text-red-600 hover:text-red-800 p-2"
                    title="Delete source"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
