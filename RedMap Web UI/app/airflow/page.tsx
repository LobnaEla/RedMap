"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Wind,
  Play,
  Pause,
  Search,
  Filter,
  CheckCircle,
  AlertCircle,
  Calendar,
  Clock,
  Activity,
  RotateCcw,
} from "lucide-react"
import { useState, useEffect } from "react"
import axios from "axios"

interface Dag {
  id: string
  name: string
  status: string
  lastRun: string
  nextRun: string
  schedule: string
  description: string
}

interface GlobalMetrics {
  totalSuccessRate: string
  totalTaskInstances: number
  avgDuration: string
}

export default function AirflowPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [dags, setDags] = useState<Dag[]>([])
  const [globalMetrics, setGlobalMetrics] = useState<GlobalMetrics>({
    totalSuccessRate: "N/A",
    totalTaskInstances: 0,
    avgDuration: "N/A",
  })
  const [error, setError] = useState<string | null>(null)

  const AIRFLOW_API_URL = "/api/airflow"
  const authHeader = {
    headers: {
      "Content-Type": "application/json",
    },
  }

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch DAG list
        const dagsResponse = await axios.get(`${AIRFLOW_API_URL}/dags`, authHeader)
        const dagList = dagsResponse.data.dags
        const dagIds = dagList.map((dag: any) => dag.dag_id)
        if (!dagList || dagList.length === 0) {
          setError("No DAGs found")
          return
        }

        // Process DAGs
        const fetchedDags = dagList.map((dag: any) => {
          const formatDate = (dateStr: string | null) => {
            return dateStr ? new Date(dateStr).toLocaleString() : 'N/A'
          }

          const formatSchedule = (scheduleObj: any) => {
            if (scheduleObj && typeof scheduleObj === 'object' && '__type' in scheduleObj) {
              const { days, seconds } = scheduleObj
              const totalHours = days * 24 + Math.floor(seconds / 3600)
              const remainingMinutes = Math.floor((seconds % 3600) / 60)
              if (totalHours > 0 && remainingMinutes > 0) {
                return `${totalHours} hours ${remainingMinutes} minutes`
              } else if (totalHours > 0) {
                return `${totalHours} hours`
              } else if (remainingMinutes > 0) {
                return `${remainingMinutes} minutes`
              }
              return 'N/A'
            }
            return scheduleObj || 'N/A'
          }

          return {
            id: dag.dag_id,
            name: dag.dag_display_name || dag.dag_id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
            status: dag.is_paused ? "paused" : "running",
            lastRun: formatDate(dag.last_parsed_time),
            nextRun: formatDate(dag.next_dagrun),
            schedule: formatSchedule(dag.schedule_interval),
            description: dag.description || "No description available",
            successRate: "N/A", // Per-DAG success rate can be calculated separately if needed
          }
        })

        // Calculate global metrics
        const now = new Date()
        const last24Hours = new Date(now.getTime() - 24 * 60 * 60 * 1000) // 24 hours ago
        const today = now.toISOString().split('T')[0] // e.g., "2025-08-06"


        // Success and Failed DAG Runs for last 24h success rate
        const [failedRunsResp, successfulRunsResp] = await Promise.all([
          await axios.get(`${AIRFLOW_API_URL}/dags/~/dagRuns`, {
            ...authHeader,
            params: {
              state: 'failed',
              limit: 1000,
              order_by: '-execution_date',
            },
          }),
          await axios.get(`${AIRFLOW_API_URL}/dags/~/dagRuns`, {
            ...authHeader,
            params: {
              state: 'success',
              limit: 1,
              order_by: '-execution_date',
            },
          })
        ])

        const recentFailed = (failedRunsResp.data.dag_runs || []).filter(
          (run: any) => new Date(run.execution_date) >= last24Hours
        )

        const recentSuccess = (successfulRunsResp.data.dag_runs || [])
          .filter((run: any) => {
            return new Date(run.execution_date) >= last24Hours
          })

        const totalRuns = recentFailed.length + recentSuccess.length
        const totalSuccessRate = totalRuns > 0
          ? `${((recentSuccess.length / totalRuns) * 100).toFixed(2)}%`
          : 'N/A'

        // Task Instances (executed today) and Avg Duration from all DAG runs
        const allRuns = [...recentSuccess, ...recentFailed]

        let todayInstances = 0
        let durations: number[] = []

        for (const run of allRuns) {
          const dagId = run.dag_id
          const dagRunId = run.dag_run_id

          try {
            const taskResp = await axios.get(`${AIRFLOW_API_URL}/dags/${dagId}/dagRuns/${dagRunId}/taskInstances`, authHeader)
            const tasks = taskResp.data.task_instances || []

            tasks.forEach((task: any) => {
              if (task.execution_date?.startsWith(today)) {
                todayInstances++
              }

              if (
                ['success', 'failed'].includes(task.state) &&
                task.start_date &&
                task.end_date
              ) {
                const start = new Date(task.start_date).getTime()
                const end = new Date(task.end_date).getTime()
                durations.push((end - start) / 1000 / 60)
              }
            })
          } catch (err) {
            console.warn(`⚠️ Failed to fetch taskInstances for ${dagId} / ${dagRunId}`)
          }
        }


        const avgDuration = durations.length > 0
          ? `${(durations.reduce((a, b) => a + b, 0) / durations.length).toFixed(2)} minutes`
          : 'N/A'

        setDags(fetchedDags)
        setGlobalMetrics({
          totalSuccessRate,
          totalTaskInstances: todayInstances,
          avgDuration,
        })
        setError(null)

      } catch (err: any) {
        setError(`Failed to fetch data: ${err.response?.data?.error || err.message}`)
      }
    }
    fetchData()
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case "running":
        return "default"
      case "success":
        return "default"
      case "paused":
        return "secondary"
      case "failed":
        return "destructive"
      default:
        return "outline"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "running":
        return <Activity className="h-4 w-4 text-blue-500" />
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case "paused":
        return <Pause className="h-4 w-4 text-yellow-500" />
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <Clock className="h-4 w-4" />
    }
  }

  const handleTriggerDag = async (dagId: string) => {
    try {
      await axios.post(
        `${AIRFLOW_API_URL}/dags/${dagId}/dagRuns`,
        { conf: {} },
        authHeader
      )
      console.log(`Triggered DAG: ${dagId}`)
    } catch (err: any) {
      console.error(`Failed to trigger DAG ${dagId}: ${err.response?.data?.error || err.message}`)
      setError(`Failed to trigger DAG ${dagId}: ${err.response?.data?.error || err.message}`)
    }
  }

  const filteredDags = dags.filter((dag) => {
    const matchesSearch =
      dag.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      dag.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === "all" || dag.status === statusFilter
    return matchesSearch && matchesStatus
  })

  return (
    <div className="w-full px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Wind className="h-8 w-8 text-cyan-600" />
          Airflow Monitoring
        </h1>
        <p className="text-muted-foreground">Monitor and manage your security data pipelines</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 text-red-700 border border-red-200 rounded-lg">
          {error}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total DAGs</CardTitle>
            <Wind className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dags.length}</div>
            <p className="text-xs text-muted-foreground">
              {dags.filter((dag) => dag.status === "running").length} running,{" "}
              {dags.filter((dag) => dag.status === "paused").length} paused
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{globalMetrics.totalSuccessRate}</div>
            <p className="text-xs text-muted-foreground">Last 24 hours</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Task Instances</CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{globalMetrics.totalTaskInstances}</div>
            <p className="text-xs text-muted-foreground">Executed today</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
            <Clock className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{globalMetrics.avgDuration}</div>
            <p className="text-xs text-muted-foreground">Per task execution</p>
          </CardContent>
        </Card>
      </div>

      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4" />
              <span className="text-sm font-medium">Filters:</span>
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="running">Running</SelectItem>
                <SelectItem value="success">Success</SelectItem>
                <SelectItem value="paused">Paused</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
              </SelectContent>
            </Select>
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search DAGs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Security Data Pipelines (DAGs)</CardTitle>
          <CardDescription>Monitor and trigger your Airflow DAGs for security operations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredDags.map((dag) => (
              <div key={dag.id} className="p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-start space-x-3 flex-1">
                    {getStatusIcon(dag.status)}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <h3 className="font-medium">{dag.name}</h3>
                        <Badge variant={getStatusColor(dag.status)}>{dag.status}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">{dag.description}</p>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          Last: {dag.lastRun}
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          Next: {dag.nextRun}
                        </span>
                        <span className="flex items-center gap-1">
                          <RotateCcw className="h-3 w-3" />
                          {dag.schedule}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleTriggerDag(dag.id)}
                      className="bg-red-50 hover:bg-red-100 text-red-700 border-red-200"
                    >
                      <Play className="h-4 w-4 mr-1" />
                      Trigger
                    </Button>
                    <Button variant="ghost" size="sm">
                      {dag.status === "paused" ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}