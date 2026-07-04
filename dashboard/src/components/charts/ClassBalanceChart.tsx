import { Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"

interface ClassBalanceChartProps {
  classBalance: Record<string, number>
}

export function ClassBalanceChart({ classBalance }: ClassBalanceChartProps) {
  const data = Object.entries(classBalance).map(([name, value]) => ({ name, value: Number(value.toFixed(2)) }))

  const config: ChartConfig = {
    value: {
      label: "Failure balance",
      color: "hsl(var(--chart-1))",
    },
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Failure balance</CardTitle>
        <CardDescription>Class distribution for failure within 24 hours</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={config} className="h-[260px] w-full">
          <BarChart data={data} margin={{ left: 8, right: 8 }}>
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis dataKey="name" tickLine={false} axisLine={false} />
            <YAxis tickFormatter={(value) => `${value}%`} tickLine={false} axisLine={false} />
            <ChartTooltip content={<ChartTooltipContent hideIndicator labelKey="name" />} />
            <Bar dataKey="value" fill="var(--color-value)" radius={[12, 12, 0, 0]} />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
