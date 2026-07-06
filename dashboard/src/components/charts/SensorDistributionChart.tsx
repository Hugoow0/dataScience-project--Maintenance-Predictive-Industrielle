import { Bar, BarChart, CartesianGrid, XAxis, YAxis, LabelList } from "recharts"

import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import type { NumericSummary } from "@/types/api"

interface SensorDistributionChartProps {
  feature: string
  summary: NumericSummary
}

export function SensorDistributionChart({ feature, summary }: SensorDistributionChartProps) {
  const data = summary.histogram.map((bin) => ({
    range: `${bin.left.toFixed(1)}–${bin.right.toFixed(1)}`,
    midpoint: ((bin.left + bin.right) / 2).toFixed(1),
    count: bin.count,
  }))

  // Show at most ~6 ticks on X so labels don't overlap
  const tickInterval = Math.max(1, Math.floor(data.length / 6))

  const config: ChartConfig = {
    count: {
      label: "Count",
      color: "var(--chart-2)",
    },
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>{feature}</CardTitle>
        <CardDescription>
          Mean {summary.mean.toFixed(2)} · Median {summary.median.toFixed(2)} · Std {summary.std.toFixed(2)}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={config} className="h-[240px] w-full">
          <BarChart data={data} margin={{ left: 0, right: 8, bottom: 32 }}>
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis
              dataKey="midpoint"
              tickLine={false}
              axisLine={false}
              interval={tickInterval - 1}
              tick={{ fontSize: 11 }}
              label={{
                value: feature,
                position: "insideBottom",
                offset: -20,
                fontSize: 11,
                fill: "var(--muted-foreground)",
              }}
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              tick={{ fontSize: 11 }}
              label={{
                value: "Count",
                angle: -90,
                position: "insideLeft",
                offset: 12,
                fontSize: 11,
                fill: "var(--muted-foreground)",
              }}
            />
            <ChartTooltip
              content={
                <ChartTooltipContent
                  labelFormatter={(_, payload) =>
                    payload?.[0]?.payload?.range ?? ""
                  }
                />
              }
            />
            <Bar dataKey="count" fill="var(--color-count)" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ChartContainer>
      </CardContent>
      <CardFooter className="text-xs text-muted-foreground pt-0">
        Min {summary.min.toFixed(2)} · Max {summary.max.toFixed(2)} · each bar = one value range
      </CardFooter>
    </Card>
  )
}
