import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import type { NumericSummary } from "@/types/api"

interface SensorDistributionChartProps {
  feature: string
  summary: NumericSummary
}

export function SensorDistributionChart({ feature, summary }: SensorDistributionChartProps) {
  const data = summary.histogram.map((bin) => ({
    range: `${bin.left.toFixed(1)}-${bin.right.toFixed(1)}`,
    count: bin.count,
  }))

  const config: ChartConfig = {
    count: {
      label: feature,
      color: "hsl(var(--chart-2))",
    },
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>{feature}</CardTitle>
        <CardDescription>
          Mean {summary.mean.toFixed(2)} | Median {summary.median.toFixed(2)}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={config} className="h-[240px] w-full">
          <BarChart data={data} margin={{ left: 8, right: 8 }}>
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis dataKey="range" tickLine={false} axisLine={false} hide />
            <YAxis tickLine={false} axisLine={false} />
            <ChartTooltip content={<ChartTooltipContent hideIndicator labelKey="range" />} />
            <Bar dataKey="count" fill="var(--color-count)" radius={[10, 10, 0, 0]} />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
