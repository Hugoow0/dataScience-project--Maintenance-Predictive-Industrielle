import { Bar, BarChart, CartesianGrid, Legend, XAxis, YAxis } from "recharts"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import type { ModelComparisonItem } from "@/types/api"

interface ModelComparisonChartProps {
  models: ModelComparisonItem[]
}

const palette = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
]

export function ModelComparisonChart({ models }: ModelComparisonChartProps) {
  const metricKeys = Array.from(
    new Set(models.flatMap((item) => Object.keys(item.metrics)))
  )

  const data = models.map((item) => ({
    model: item.model,
    ...Object.fromEntries(metricKeys.map((metric) => [metric, item.metrics[metric] ?? 0])),
  }))

  const config = metricKeys.reduce<ChartConfig>((accumulator, metric, index) => {
    accumulator[metric] = {
      label: metric.toUpperCase(),
      color: palette[index % palette.length],
    }
    return accumulator
  }, {})

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Model comparison</CardTitle>
        <CardDescription>Precomputed metrics loaded from the backend</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={config} className="h-[320px] w-full">
          <BarChart data={data} margin={{ left: 8, right: 8 }}>
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis dataKey="model" tickLine={false} axisLine={false} />
            <YAxis tickLine={false} axisLine={false} domain={[0, 1]} />
            <ChartTooltip content={<ChartTooltipContent hideIndicator />} />
            <Legend />
            {metricKeys.map((metric) => (
              <Bar key={metric} dataKey={metric} fill={`var(--color-${metric})`} radius={[10, 10, 0, 0]} />
            ))}
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
