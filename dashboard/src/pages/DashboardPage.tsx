import { useEffect, useState } from "react"
import { toast } from "sonner"

import { api } from "@/lib/api"
import type { DatasetStatsResponse, ModelComparisonResponse } from "@/types/api"
import { KpiCard } from "@/components/KpiCard"
import { ClassBalanceChart } from "@/components/charts/ClassBalanceChart"
import { SensorDistributionChart } from "@/components/charts/SensorDistributionChart"
import { CorrelationHeatmap } from "@/components/charts/CorrelationHeatmap"
import { ModelComparisonChart } from "@/components/charts/ModelComparisonChart"
import { Skeleton } from "@/components/ui/skeleton"

const SENSOR_FEATURES = ["vibration_rms", "temperature_motor", "pressure_level"]

function DashboardSkeleton() {
  return (
    <div className="grid gap-4">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-28" />
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <Skeleton className="h-80" />
        <Skeleton className="h-80" />
      </div>
      <Skeleton className="h-96" />
    </div>
  )
}

export function DashboardPage() {
  const [stats, setStats] = useState<DatasetStatsResponse | null>(null)
  const [comparison, setComparison] = useState<ModelComparisonResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true

    async function loadDashboard() {
      try {
        const [statsResponse, comparisonResponse] = await Promise.all([
          api.datasetStats(),
          api.modelComparison(),
        ])

        if (!active) {
          return
        }

        setStats(statsResponse)
        setComparison(comparisonResponse)
      } catch (error) {
        toast.error(error instanceof Error ? error.message : "Failed to load dashboard data")
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    loadDashboard()

    return () => {
      active = false
    }
  }, [])

  if (loading || !stats || !comparison) {
    return <DashboardSkeleton />
  }

  const modelCount = comparison.models.length
  const failureRate = stats.class_balance.failure ?? 0
  const dateRange = stats.date_range ? `${stats.date_range.start.slice(0, 10)} → ${stats.date_range.end.slice(0, 10)}` : "Unavailable"

  return (
    <div className="grid gap-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Total records" value={stats.row_count.toLocaleString()} description="Loaded from the cleaned dataset" />
        <KpiCard label="Failure rate" value={`${failureRate.toFixed(1)}%`} description="Share of failure_within_24h = 1" />
        <KpiCard label="Models available" value={String(modelCount)} description="Loaded from the models directory" />
        <KpiCard label="Dataset date range" value={dateRange} description="Based on the raw timestamp column" />
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <ClassBalanceChart classBalance={stats.class_balance} />
        <ModelComparisonChart models={comparison.models} />
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        {SENSOR_FEATURES.map((feature) => {
          const summary = stats.numeric_summary[feature]
          return summary ? <SensorDistributionChart key={feature} feature={feature} summary={summary} /> : null
        })}
      </section>

      <CorrelationHeatmap correlations={stats.correlation_matrix} />
    </div>
  )
}
