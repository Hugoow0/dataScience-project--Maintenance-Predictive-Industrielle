import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

interface KpiCardProps {
  label: string
  value: string
  description?: string
}

export function KpiCard({ label, value, description }: KpiCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-3xl font-semibold">{value}</CardTitle>
      </CardHeader>
      {description ? <CardContent className="text-sm text-muted-foreground">{description}</CardContent> : null}
    </Card>
  )
}
