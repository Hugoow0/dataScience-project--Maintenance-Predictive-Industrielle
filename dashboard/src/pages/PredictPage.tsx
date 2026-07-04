import { useEffect, useMemo, useState } from "react"
import { toast } from "sonner"

import { api } from "@/lib/api"
import type { DatasetStatsResponse, ModelInfoResponse } from "@/types/api"
import { PredictionForm } from "@/components/PredictionForm"
import { Skeleton } from "@/components/ui/skeleton"

function PredictSkeleton() {
  return <Skeleton className="h-[720px] w-full" />
}

export function PredictPage() {
  const [stats, setStats] = useState<DatasetStatsResponse | null>(null)
  const [models, setModels] = useState<ModelInfoResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true

    async function loadInputs() {
      try {
        const [statsResponse, modelResponse] = await Promise.all([
          api.datasetStats(),
          api.modelInfo(),
        ])

        if (!active) {
          return
        }

        setStats(statsResponse)
        setModels(modelResponse)
      } catch (error) {
        toast.error(error instanceof Error ? error.message : "Failed to load prediction inputs")
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    loadInputs()

    return () => {
      active = false
    }
  }, [])

  const defaults = useMemo(() => {
    if (!stats || !models) {
      return null
    }

    const firstModel = models.models[0]?.model ?? ""
    const operatingModes = Object.keys(stats.categorical_summary.operating_mode ?? {})
    const defaultOperatingMode = operatingModes.includes("normal") ? "normal" : operatingModes[0] ?? "idle"

    return {
      model: firstModel,
      operating_mode: defaultOperatingMode,
      vibration_rms: stats.numeric_summary.vibration_rms?.mean ?? 0,
      temperature_motor: stats.numeric_summary.temperature_motor?.mean ?? 0,
      current_phase_avg: stats.numeric_summary.current_phase_avg?.mean ?? 0,
      pressure_level: stats.numeric_summary.pressure_level?.mean ?? 0,
      rpm: stats.numeric_summary.rpm?.mean ?? 0,
      hours_since_maintenance: stats.numeric_summary.hours_since_maintenance?.mean ?? 0,
      ambient_temp: stats.numeric_summary.ambient_temp?.mean ?? 0,
    }
  }, [models, stats])

  if (loading || !stats || !models || !defaults) {
    return <PredictSkeleton />
  }

  const operatingModes = Object.keys(stats.categorical_summary.operating_mode ?? {})

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Live prediction</h1>
        <p className="text-sm text-muted-foreground">Select a model, adjust the sensor values, and call the API-backed inference endpoint.</p>
      </div>

      <PredictionForm models={models.models} stats={stats} operatingModes={operatingModes} initialValues={defaults} />
    </div>
  )
}
