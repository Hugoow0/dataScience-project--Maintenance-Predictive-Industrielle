import { zodResolver } from "@hookform/resolvers/zod"
import { useEffect, useState } from "react"
import { Controller, useForm, type Resolver } from "react-hook-form"
import { z } from "zod"

import { api, ApiError } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import type { DatasetStatsResponse, ModelInfoItem, PredictResponse, ApiValidationError } from "@/types/api"
import { ModelSelector } from "@/components/ModelSelector"

const schema = z.object({
  model: z.string().min(1, "Choose a model"),
  operating_mode: z.string().min(1, "Choose an operating mode"),
  vibration_rms: z.coerce.number().positive("Must be greater than zero"),
  temperature_motor: z.coerce.number().min(-20).max(200),
  current_phase_avg: z.coerce.number().min(0),
  pressure_level: z.coerce.number().min(0),
  rpm: z.coerce.number().min(0),
  hours_since_maintenance: z.coerce.number().min(0),
  ambient_temp: z.coerce.number().min(-50).max(100),
})

type PredictionFormValues = z.infer<typeof schema>

interface PredictionFormProps {
  models: ModelInfoItem[]
  stats: DatasetStatsResponse
  operatingModes: string[]
  initialValues: PredictionFormValues
}

function buildPayload(values: PredictionFormValues) {
  return {
    model: values.model,
    features: {
      vibration_rms: values.vibration_rms,
      temperature_motor: values.temperature_motor,
      current_phase_avg: values.current_phase_avg,
      pressure_level: values.pressure_level,
      rpm: values.rpm,
      operating_mode: values.operating_mode,
      hours_since_maintenance: values.hours_since_maintenance,
      ambient_temp: values.ambient_temp,
    },
  }
}

function isValidationArray(detail: unknown): detail is ApiValidationError[] {
  return Array.isArray(detail)
}

export function PredictionForm({ models, stats, operatingModes, initialValues }: PredictionFormProps) {
  const [result, setResult] = useState<PredictResponse | null>(null)

  const form = useForm<PredictionFormValues>({
    resolver: zodResolver(schema) as Resolver<PredictionFormValues>,
    defaultValues: initialValues,
  })

  useEffect(() => {
    form.reset(initialValues)
  }, [form, initialValues])

  const onSubmit = form.handleSubmit(async (values: PredictionFormValues) => {
    setResult(null)
    try {
      const response = await api.predict(buildPayload(values))
      setResult(response)
    } catch (error) {
      if (error instanceof ApiError && isValidationArray(error.payload?.detail)) {
        error.payload.detail.forEach((item) => {
          const field = item.loc.at(-1)
          if (typeof field === "string" && field in values) {
            form.setError(field as keyof PredictionFormValues, {
              message: item.msg,
            })
          }
        })
        return
      }

      form.setError("root", {
        message: error instanceof ApiError ? String(error.payload?.detail ?? error.message) : "Prediction failed",
      })
    }
  })

  const resetForm = () => {
    form.reset(initialValues)
    setResult(null)
  }

  const renderResult = () => {
    if (!result) {
      return null
    }

    if (result.task_type === "regression") {
      return (
        <Card>
          <CardHeader>
            <CardDescription>Regression output</CardDescription>
            <CardTitle className="text-3xl">{result.prediction.toFixed(1)} {result.unit}</CardTitle>
          </CardHeader>
        </Card>
      )
    }

    const confidence = Math.round(result.probability * 100)
    const failure = result.label === "failure"

    return (
      <Card>
        <CardHeader>
          <CardDescription>Classification output</CardDescription>
          <div className="flex items-center gap-2">
            <Badge variant={failure ? "destructive" : "secondary"}>
              Failure risk: {failure ? "HIGH" : "LOW"}
            </Badge>
            <span className="text-sm text-muted-foreground">{result.model}</span>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span>Confidence</span>
            <span>{confidence}%</span>
          </div>
          <div className="h-3 rounded-full bg-muted">
            <div
              className={`h-3 rounded-full ${failure ? "bg-destructive" : "bg-emerald-500"}`}
              style={{ width: `${confidence}%` }}
            />
          </div>
          <div className="text-sm text-muted-foreground">Predicted label: {result.label}</div>
        </CardContent>
      </Card>
    )
  }

  const rootError = form.formState.errors.root?.message

  return (
    <div className="grid gap-6 lg:grid-cols-[1.4fr_0.9fr]">
      <Card>
        <CardHeader>
          <CardTitle>Predict machine status</CardTitle>
          <CardDescription>Use the API-backed model to estimate maintenance risk in real time.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4" onSubmit={onSubmit}>
            <div className="grid gap-2">
              <label className="text-sm font-medium">Model</label>
              <Controller
                control={form.control}
                name="model"
                render={({ field }) => (
                  <ModelSelector models={models} value={field.value} onValueChange={field.onChange} />
                )}
              />
              {form.formState.errors.model ? <p className="text-sm text-destructive">{form.formState.errors.model.message}</p> : null}
            </div>

            <div className="grid gap-2">
              <label className="text-sm font-medium">Operating mode</label>
              <Controller
                control={form.control}
                name="operating_mode"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select operating mode" />
                    </SelectTrigger>
                    <SelectContent>
                      {operatingModes.map((mode) => (
                        <SelectItem key={mode} value={mode}>
                          {mode}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
              {form.formState.errors.operating_mode ? <p className="text-sm text-destructive">{form.formState.errors.operating_mode.message}</p> : null}
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {[
                ["vibration_rms", "Vibration RMS"],
                ["temperature_motor", "Motor temperature"],
                ["current_phase_avg", "Current phase avg"],
                ["pressure_level", "Pressure level"],
                ["rpm", "RPM"],
                ["hours_since_maintenance", "Hours since maintenance"],
                ["ambient_temp", "Ambient temperature"],
              ].map(([name, label]) => (
                <div key={name} className="grid gap-2">
                  <label className="text-sm font-medium">{label}</label>
                  <Input type="number" step="any" {...form.register(name as keyof PredictionFormValues)} />
                  {form.formState.errors[name as keyof PredictionFormValues] ? (
                    <p className="text-sm text-destructive">
                      {form.formState.errors[name as keyof PredictionFormValues]?.message}
                    </p>
                  ) : null}
                </div>
              ))}
            </div>

            {rootError ? <p className="rounded-2xl bg-destructive/10 px-3 py-2 text-sm text-destructive">{rootError}</p> : null}

            <div className="flex flex-wrap gap-3 pt-2">
              <Button type="submit" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting ? "Predicting..." : "Predict"}
              </Button>
              <Button type="button" variant="outline" onClick={resetForm}>
                Reset
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <div className="grid gap-4">
        <Card>
          <CardHeader>
            <CardDescription>Dataset defaults</CardDescription>
            <CardTitle className="text-lg">{stats.row_count.toLocaleString()} records</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 text-sm text-muted-foreground">
            <div>Selected model: {initialValues.model}</div>
            <div>Operating mode options: {operatingModes.join(", ")}</div>
          </CardContent>
        </Card>
        {renderResult()}
      </div>
    </div>
  )
}
