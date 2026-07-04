import { Pie, PieChart, Cell } from "recharts"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"

interface ClassBalanceChartProps {
  classBalance: Record<string, number>
}

export function ClassBalanceChart({ classBalance }: ClassBalanceChartProps) {
  const entries = Object.entries(classBalance)

  const sliceColor = (name: string): string => {
    const key = name.toLowerCase()
    if (key.includes("no_failure") || key.includes("no failure")) return "oklch(0.65 0.22 142)" // green
    if (key.includes("failure"))                                   return "oklch(0.62 0.22  20)" // red
    return `var(--chart-${(Object.keys(classBalance).indexOf(name) % 5) + 1})`
  }

  const data = entries.map(([name, value]) => ({
    name,
    value: Number(value.toFixed(2)),
    fill: sliceColor(name),
  }))

  // Config keys must match the `name` field in data so ChartLegendContent
  // can look up label + color from the Recharts legend payload.
  const config: ChartConfig = Object.fromEntries(
    entries.map(([name]) => [
      name,
      { label: name, color: sliceColor(name) },
    ])
  )

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Failure balance</CardTitle>
        <CardDescription>Class distribution for failure within 24 hours</CardDescription>
      </CardHeader>
      <CardContent className="flex items-center justify-center pb-4">
        <ChartContainer config={config} className="h-[260px] w-full">
          <PieChart>
            <ChartTooltip
              cursor={false}
              content={<ChartTooltipContent nameKey="name" hideLabel />}
            />
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={70}
              outerRadius={110}
              paddingAngle={3}
              strokeWidth={0}
            >
              {data.map((entry, index) => (
                <Cell key={entry.name} fill={entry.fill} />
              ))}
            </Pie>
            <ChartLegend content={<ChartLegendContent nameKey="name" />} />
          </PieChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
