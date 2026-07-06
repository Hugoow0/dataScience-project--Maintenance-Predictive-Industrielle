import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import type { CorrelationPoint } from "@/types/api"

interface CorrelationHeatmapProps {
  correlations: CorrelationPoint[]
}

export function CorrelationHeatmap({ correlations }: CorrelationHeatmapProps) {
  const sensors = Array.from(new Set(correlations.flatMap((item) => [item.x, item.y])))

  const lookup = new Map<string, number>()
  correlations.forEach((item) => {
    lookup.set(`${item.x}::${item.y}`, item.value)
    lookup.set(`${item.y}::${item.x}`, item.value)
  })

  const colorForValue = (value: number) => {
    const alpha = Math.min(Math.abs(value), 1)
    return value >= 0 ? `rgba(34, 197, 94, ${0.12 + alpha * 0.65})` : `rgba(239, 68, 68, ${0.12 + alpha * 0.65})`
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Correlation matrix</CardTitle>
        <CardDescription>Pearson correlation between the sensor features</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-40">Feature</TableHead>
              {sensors.map((sensor) => (
                <TableHead key={sensor} className="text-center text-xs">
                  {sensor}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {sensors.map((row) => (
              <TableRow key={row}>
                <TableCell className="font-medium">{row}</TableCell>
                {sensors.map((column) => {
                  const value = row === column ? 1 : lookup.get(`${row}::${column}`) ?? 0
                  return (
                    <TableCell key={column} className="text-center">
                      <span
                        className="inline-flex min-w-14 items-center justify-center rounded-xl px-2 py-1 text-xs font-medium"
                        style={{ backgroundColor: colorForValue(value) }}
                      >
                        {value.toFixed(2)}
                      </span>
                    </TableCell>
                  )
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
