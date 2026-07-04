import { useEffect, useState } from "react"
import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom"
import { Activity, Radar, Sparkles } from "lucide-react"

import { api } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { buttonVariants } from "@/components/ui/button"
import { Toaster } from "@/components/ui/sonner"
import { DashboardPage } from "@/pages/DashboardPage"
import { PredictPage } from "@/pages/PredictPage"
import { cn } from "@/lib/utils"

function AppShell() {
  const [health, setHealth] = useState<"loading" | "online" | "offline">("loading")

  useEffect(() => {
    let active = true

    const ping = async () => {
      try {
        await api.health()
        if (active) {
          setHealth("online")
        }
      } catch {
        if (active) {
          setHealth("offline")
        }
      }
    }

    ping()
    const timer = window.setInterval(ping, 60000)

    return () => {
      active = false
      window.clearInterval(timer)
    }
  }, [])

  return (
    <div className="min-h-svh bg-[radial-gradient(circle_at_top_left,_rgba(34,197,94,0.08),_transparent_35%),radial-gradient(circle_at_top_right,_rgba(59,130,246,0.10),_transparent_25%),linear-gradient(180deg,theme(colors.background),theme(colors.background))] text-foreground">
      <Toaster richColors closeButton />
      <header className="sticky top-0 z-30 border-b border-border/70 bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <div>
            <div className="flex items-center gap-2 text-sm font-medium uppercase tracking-[0.24em] text-muted-foreground">
              Predictive maintenance
            </div>
            <h1 className="text-lg font-semibold">Industrial intelligence dashboard</h1>
          </div>

          <nav className="flex items-center gap-2">
            <NavLink to="/" end>
              {({ isActive }) => (
                <span
                  className={cn(
                    buttonVariants({ variant: isActive ? "default" : "ghost", size: "sm" }),
                    "gap-1.5"
                  )}
                >
                  <Radar className="size-4" />
                  Dashboard
                </span>
              )}
            </NavLink>
            <NavLink to="/predict">
              {({ isActive }) => (
                <span
                  className={cn(
                    buttonVariants({ variant: isActive ? "default" : "ghost", size: "sm" }),
                    "gap-1.5"
                  )}
                >
                  <Activity className="size-4" />
                  Predict
                </span>
              )}
            </NavLink>
            <Badge variant={health === "online" ? "default" : health === "loading" ? "secondary" : "destructive"}>
              API {health}
            </Badge>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/predict" element={<PredictPage />} />
        </Routes>
      </main>
    </div>
  )
}

export function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  )
}

export default App
