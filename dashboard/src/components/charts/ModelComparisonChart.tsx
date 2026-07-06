import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import type { ModelComparisonItem } from "@/types/api"

interface ModelComparisonChartProps {
  models: ModelComparisonItem[]
}

const CHART_KEYS = ["chart-1", "chart-2", "chart-3", "chart-4", "chart-5"] as const

// Shorten long model names so they fit in the legend
function shortName(name: string): string {
  return name
    .replace("modele_", "")
    .replace("_maintenance", "")
    .replace("logistic_regression", "log_reg")
    .replace("random_forest", "rand_forest")
}

export function ModelComparisonChart({ models }: ModelComparisonChartProps) {
  // All unique metric names across all models
  const metricKeys = Array.from(
    new Set(models.flatMap((item) => Object.keys(item.metrics)))
  ).sort()

  // Pivot: one row per metric, one column per model
  // e.g. { metric: "accuracy", logistic_regression: 0.94, random_forest: 0.98, ... }
  const data = metricKeys.map((metric) => ({
    metric,
    ...Object.fromEntries(
      models.map((item) => [item.model, item.metrics[metric] ?? 0])
    ),
  }))

  // Each model gets its own chart-N key so ChartContainer injects --color-chart-N
  const modelToChartKey = Object.fromEntries(
    models.map((item, index) => [item.model, CHART_KEYS[index % CHART_KEYS.length]])
  )

  const config: ChartConfig = Object.fromEntries(
    models.map((item, index) => [
      item.model,
      {
        label: shortName(item.model),
        color: `var(--chart-${(index % 5) + 1})`,
      },
    ])
  )

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Model comparison</CardTitle>
        <CardDescription>Precomputed metrics — one bar per model, grouped by metric</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={config} className="h-[320px] w-full">
          <BarChart data={data} margin={{ left: 8, right: 8, bottom: 8 }}>
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis
              dataKey="metric"
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 12 }}
              tickFormatter={(v: string) => v.toUpperCase()}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              domain={[0, 1]}
              tick={{ fontSize: 11 }}
              tickFormatter={(v: number) => v.toFixed(2)}
            />
            <ChartTooltip
              content={
                <ChartTooltipContent
                  labelFormatter={(label) => String(label).toUpperCase()}
                  formatter={(value, name) => [
                    Number(value).toFixed(3) + ": ",
                    config[name as string]?.label ?? name,
                  ]}
                />
              }
            />
            <ChartLegend content={<ChartLegendContent />} />
            {models.map((item) => (
              <Bar
                key={item.model}
                dataKey={item.model}
                name={item.model}
                fill={`var(--color-${item.model})`}
                radius={[6, 6, 0, 0]}
              />
            ))}
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
