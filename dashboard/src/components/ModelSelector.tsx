import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import type { ModelInfoItem } from "@/types/api"

interface ModelSelectorProps {
  models: ModelInfoItem[]
  value: string
  onValueChange: (value: string) => void
}

export function ModelSelector({ models, value, onValueChange }: ModelSelectorProps) {
  return (
    <Select value={value} onValueChange={(nextValue) => onValueChange(nextValue ?? "")}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder="Select a model" />
      </SelectTrigger>
      <SelectContent>
        {models.map((model) => (
          <SelectItem key={model.model} value={model.model}>
            {model.model}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
