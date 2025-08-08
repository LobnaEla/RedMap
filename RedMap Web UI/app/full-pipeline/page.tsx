"use client"

import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
    Wind,
    Play,
    Search,
    Filter,
    CheckCircle,
    AlertCircle,
    Activity,
    Clock,
    Eye,
    ChevronDown,
    Database,
    RefreshCw,
    Zap,
    Timer,
    Users,
} from "lucide-react"

interface PipelineStep {
    id: string
    name: string
    status: "completed" | "in-progress" | "failed" | "pending"
    dagId?: string
    source?: string
    nextSteps?: string[]
    lastRun?: string
    duration?: number
}

interface Task {
    task_id: string
    state?: "success" | "running" | "failed" | "pending"
    start_date?: string
    duration?: number
}

interface EventSource {
    name: string
    status: "ready" | "rate_limited" | "error" | "monitoring"
    last_trigger?: string
    cooldown_remaining_minutes?: number
    can_trigger: boolean
    metadata?: any
}

interface DAGRun {
    dag_id: string
    state: "success" | "running" | "failed" | "pending"
    execution_date: string
    duration?: number
}

export default function DynamicPipelinePage() {
    const [steps, setSteps] = useState<PipelineStep[]>([])
    const [eventSources, setEventSources] = useState<EventSource[]>([])
    const [error, setError] = useState<string | null>(null)
    const [loading, setLoading] = useState(true)
    const [searchTerm, setSearchTerm] = useState("")
    const [statusFilter, setStatusFilter] = useState("all")
    const [preprocessTasks, setPreprocessTasks] = useState<Task[]>([])
    const [showEventDetails, setShowEventDetails] = useState<Record<string, boolean>>({})
    const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
    const [isConnected, setIsConnected] = useState(false)

    const AIRFLOW_API_URL = "/api/airflow"
    const EVENT_API_URL = "/api/event-service"
    const authHeader = { headers: { "Content-Type": "application/json" } }

    // Get refresh interval from environment or use default
    const REFRESH_INTERVAL = parseInt(process.env.NEXT_PUBLIC_MONITORING_REFRESH_INTERVAL || "30000")

    // Fetch event sources status from Event Monitor service
    const fetchEventSources = useCallback(async () => {
        try {
            const response = await fetch(`${EVENT_API_URL}/sources/status`, authHeader)
            if (response.ok) {
                const data = await response.json()
                console.log('🔍 DEBUG - Raw event sources data:', data)

                const sources: EventSource[] = Object.entries(data).map(([name, status]: [string, any]) => {
                    console.log(`🔍 DEBUG - Processing source ${name}:`, status)
                    return {
                        name,
                        status: status.status,
                        last_trigger: status.last_trigger,
                        cooldown_remaining_minutes: status.cooldown_remaining_minutes,
                        can_trigger: status.can_trigger,
                        metadata: status.metadata
                    }
                })
                console.log('🔍 DEBUG - Processed event sources:', sources)
                setEventSources(sources)
                setIsConnected(true)
            } else {
                throw new Error(`HTTP ${response.status}`)
            }
        } catch (err: any) {
            console.error('Event sources fetch error:', err)
            setIsConnected(false)
        }
    }, [])

    // Fetch pipeline data dynamically from Airflow
    const fetchPipelineData = useCallback(async () => {
        setLoading(true)
        try {
            // Get all DAGs from Airflow
            const dagsResponse = await fetch(`${AIRFLOW_API_URL}/dags`, authHeader)
            if (!dagsResponse.ok) throw new Error('Failed to fetch DAGs')

            const dagsData = await dagsResponse.json()
            const dagList = dagsData.dags || []

            // Get DAG runs for status - ordered by execution_date descending to get latest first
            const dagRunsResponse = await fetch(`${AIRFLOW_API_URL}/dags/~/dagRuns?limit=100&order_by=-execution_date`, authHeader)
            const dagRunsData = dagRunsResponse.ok ? await dagRunsResponse.json() : { dag_runs: [] }
            const dagRuns: DAGRun[] = dagRunsData.dag_runs || []

            console.log('🔍 DEBUG - Raw DAG runs data:', dagRuns.slice(0, 5)) // Show first 5 for brevity
            console.log('🔍 DEBUG - Total DAG runs fetched:', dagRuns.length)

            // Detect ingestion DAGs dynamically
            const ingestionDags = dagList.filter((dag: any) =>
                dag.dag_id.startsWith("cti_pipeline_")
            )

            const sources = ingestionDags.map((dag: any) =>
                dag.dag_id.replace("cti_pipeline_", "")
            )

            // Get latest run status for each DAG
            const getLatestRunStatus = (dagId: string) => {
                const runs = dagRuns.filter(run => run.dag_id === dagId)
                if (runs.length === 0) return "pending"

                // Since dagRuns is already ordered by execution_date desc, first match is the latest
                const latestRun = runs[0]

                return latestRun.state === "success" ? "completed" :
                    latestRun.state === "running" ? "in-progress" :
                        latestRun.state === "failed" ? "failed" : "pending"
            }

            // Get latest run date for each DAG
            const getLatestRunDate = (dagId: string) => {
                const runs = dagRuns.filter(run => run.dag_id === dagId)
                if (runs.length === 0) return undefined

                // Since dagRuns is already ordered by execution_date desc, first match is the latest
                const latestRun = runs[0]

                console.log(`🔍 DEBUG - Latest run for ${dagId}:`, latestRun)
                return latestRun.execution_date
            }

            // Build pipeline steps dynamically
            const pipelineSteps: PipelineStep[] = [
                // Dynamic ingestion steps
                ...sources.map((source: string) => ({
                    id: `cti-ingestion-${source}`,
                    name: `CTI Ingestion (${source.toUpperCase()})`,
                    status: getLatestRunStatus(`cti_pipeline_${source}`),
                    dagId: `cti_pipeline_${source}`,
                    source,
                    nextSteps: ["preprocess_pipeline"],
                    lastRun: getLatestRunDate(`cti_pipeline_${source}`),
                })),

                // Core pipeline steps - detected dynamically
                {
                    id: "preprocess_pipeline",
                    name: "Preprocess",
                    status: getLatestRunStatus("preprocess_pipeline"),
                    dagId: "preprocess_pipeline",
                    nextSteps: ["llm_mitre_mapping", "rag_pipeline"],
                    lastRun: getLatestRunDate("preprocess_pipeline"),
                },
                {
                    id: "llm_mitre_mapping",
                    name: "LLM MITRE Mapping",
                    status: getLatestRunStatus("llm_mitre_mapping"),
                    dagId: "llm_mitre_mapping",
                    nextSteps: ["llm_judge_dag"],
                    lastRun: getLatestRunDate("llm_mitre_mapping"),
                },
                {
                    id: "rag_pipeline",
                    name: "Retrieval Augmented Search",
                    status: getLatestRunStatus("rag_pipeline"),
                    dagId: "rag_pipeline",
                    nextSteps: ["llm_judge_dag"],
                    lastRun: getLatestRunDate("rag_pipeline"),
                },
                {
                    id: "llm_judge_dag",
                    name: "LLM-as-a-Judge",
                    status: getLatestRunStatus("llm_judge_dag"),
                    dagId: "llm_judge_dag",
                    lastRun: getLatestRunDate("llm_judge_dag"),
                }
            ]

            setSteps(pipelineSteps)
            setError(null)
        } catch (err: any) {
            setError(`Failed to fetch pipeline data: ${err.message}`)
        } finally {
            setLoading(false)
            setLastUpdate(new Date())
        }
    }, [])

    // Fetch tasks for Preprocess DAG
    const fetchPreprocessTasks = useCallback(async () => {
        try {
            const response = await fetch(`${AIRFLOW_API_URL}/dags/preprocess_pipeline/tasks`, authHeader)
            if (response.ok) {
                const data = await response.json()
                const tasks = data.tasks || []

                // Get task instances for current status
                const taskInstancesResponse = await fetch(
                    `${AIRFLOW_API_URL}/dags/preprocess_pipeline/dagRuns/latest/taskInstances`,
                    authHeader
                )

                let taskInstances = []
                if (taskInstancesResponse.ok) {
                    const instancesData = await taskInstancesResponse.json()
                    taskInstances = instancesData.task_instances || []
                }

                const enrichedTasks = tasks.map((task: any) => {
                    const instance = taskInstances.find((ti: any) => ti.task_id === task.task_id)
                    return {
                        task_id: task.task_id,
                        start_date: instance?.start_date,
                        duration: instance?.duration
                    }
                })

                setPreprocessTasks(enrichedTasks)
            }
        } catch (err: any) {
            console.error(`Failed to fetch Preprocess tasks: ${err.message}`)
        }
    }, [])

    // Manual trigger for Event Sources
    const handleTriggerEventSource = async (sourceName: string) => {
        try {
            const response = await fetch(`${EVENT_API_URL}/trigger`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_name: sourceName,
                    event_type: 'manual',
                    reason: 'Manual trigger from dashboard',
                    priority: 'medium'
                })
            })

            const result = await response.json()
            if (result.status === 'triggered') {
                // Refresh data after trigger
                setTimeout(() => {
                    fetchPipelineData()
                    fetchEventSources()
                }, 2000)
            } else {
                setError(`Failed to trigger ${sourceName}: ${result.message || 'Unknown error'}`)
            }
        } catch (err: any) {
            setError(`Failed to trigger ${sourceName}: ${err.message}`)
        }
    }

    // Trigger DAG directly via Airflow
    const handleTriggerDAG = async (dagId: string | undefined) => {
        if (!dagId) return
        try {
            const response = await fetch(`${AIRFLOW_API_URL}/dags/${dagId}/dagRuns`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    conf: {},
                    dag_run_id: `manual_${Date.now()}`
                })
            })

            if (response.ok) {
                // Refresh data after trigger
                setTimeout(() => {
                    fetchPipelineData()
                    if (dagId === "preprocess_pipeline") fetchPreprocessTasks()
                }, 1000)
            } else {
                const errorData = await response.json()
                setError(`Failed to trigger DAG ${dagId}: ${errorData.detail || 'Unknown error'}`)
            }
        } catch (err: any) {
            setError(`Failed to trigger DAG ${dagId}: ${err.message}`)
        }
    }

    // Auto-refresh data
    useEffect(() => {
        const fetchData = async () => {
            await Promise.all([
                fetchPipelineData(),
                fetchPreprocessTasks(),
                fetchEventSources()
            ])
        }

        fetchData()

        const interval = setInterval(fetchData, REFRESH_INTERVAL)
        return () => clearInterval(interval)
    }, [fetchPipelineData, fetchPreprocessTasks, fetchEventSources])

    const getStatusColor = (status: string) => {
        switch (status) {
            case "completed":
            case "success":
            case "ready":
                return "bg-[hsl(var(--status-success-bg))] text-[hsl(var(--status-success-text))] border-[hsl(var(--status-success-border))]"
            case "in-progress":
            case "running":
            case "monitoring":
                return "bg-[hsl(var(--status-warning-bg))] text-[hsl(var(--status-warning-text))] border-[hsl(var(--status-warning-border))]"
            case "failed":
            case "error":
                return "bg-[hsl(var(--status-error-bg))] text-[hsl(var(--status-error-text))] border-[hsl(var(--status-error-border))]"
            case "pending":
                return "bg-[hsl(var(--status-pending-bg))] text-[hsl(var(--status-pending-text))] border-[hsl(var(--status-pending-border))]"
            case "rate_limited":
                return "bg-[hsl(var(--status-ratelimited-bg))] text-[hsl(var(--status-ratelimited-text))] border-[hsl(var(--status-ratelimited-border))]"
            default:
                return "bg-[hsl(var(--status-pending-bg))] text-[hsl(var(--status-pending-text))] border-[hsl(var(--status-pending-border))]"
        }
    }

    const getStatusIcon = (status: string) => {
        switch (status) {
            case "completed":
            case "success":
            case "ready": return <CheckCircle className="h-4 w-4 text-green-500" />
            case "in-progress":
            case "running":
            case "monitoring": return <Activity className="h-4 w-4 text-yellow-500" />
            case "failed":
            case "error": return <AlertCircle className="h-4 w-4 text-red-500" />
            case "rate_limited": return <Timer className="h-4 w-4 text-orange-500" />
            case "pending": return <Clock className="h-4 w-4 text-gray-500" />
            default: return <Clock className="h-4 w-4 text-gray-500" />
        }
    }

    const formatLastRun = (dateStr?: string) => {
        if (!dateStr) return "Never"

        console.log('🔍 DEBUG - formatLastRun input:', dateStr)

        try {
            // Handle different date formats from Airflow
            let date: Date
            if (dateStr.includes('T')) {
                // ISO format: "2025-08-08T14:30:00+00:00" or "2025-08-08T14:30:00.123456+00:00"
                date = new Date(dateStr)
            } else {
                // Other formats, let Date constructor handle it
                date = new Date(dateStr)
            }

            // Check if date is valid
            if (isNaN(date.getTime())) {
                console.warn('Invalid date string:', dateStr)
                return "Invalid date"
            }

            const now = new Date()
            const diff = now.getTime() - date.getTime()
            const minutes = Math.floor(diff / 60000)

            console.log(`🔍 DEBUG - formatLastRun: ${dateStr} -> parsed: ${date.toISOString()} -> now: ${now.toISOString()} -> diff: ${minutes}m`)

            if (minutes < 1) return "Just now"
            if (minutes < 60) return `${minutes}m ago`
            const hours = Math.floor(minutes / 60)
            if (hours < 24) return `${hours}h ago`
            const days = Math.floor(hours / 24)
            return `${days}d ago`
        } catch (error) {
            console.error('Error parsing date:', dateStr, error)
            return "Error parsing date"
        }
    }

    const filteredSteps = steps.filter(step =>
        step.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (step.source?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false)
    ).filter(step => statusFilter === "all" || step.status === statusFilter)

    const ingestionSteps = filteredSteps.filter(step => step.id.startsWith("cti-ingestion-"))
    const preprocessStep = filteredSteps.find(step => step.id === "preprocess_pipeline")
    const llmStep = filteredSteps.find(step => step.id === "llm_mitre_mapping")
    const ragStep = filteredSteps.find(step => step.id === "rag_pipeline")
    const judgeStep = filteredSteps.find(step => step.id === "llm_judge_dag")

    return (
        <div className="w-full px-4 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold flex items-center gap-3">
                    <Wind className="h-8 w-8 text-cyan-600" />
                    CTI Pipeline Monitoring
                </h1>
                <p className="text-muted-foreground">Event-driven security data pipeline with real-time monitoring</p>
            </div>

            <div className="flex items-center gap-4 mb-8">
                <div className={`flex items-center gap-2 px-3 py-2 rounded-lg ${isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                    <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                    <span className="text-sm font-medium">{isConnected ? 'Connected' : 'Offline'}</span>
                </div>
                <div className="text-sm text-muted-foreground">
                    Last updated: {formatLastRun(lastUpdate.toISOString())}
                </div>
                <button
                    onClick={() => {
                        fetchPipelineData()
                        fetchEventSources()
                        fetchPreprocessTasks()
                    }}
                    className="p-2 border border-border rounded-lg hover:bg-muted"
                >
                    <RefreshCw className="h-4 w-4" />
                </button>
            </div>

            {error && (
                <div className="mb-6 p-4 bg-red-50 text-red-700 border border-red-200 rounded-lg">
                    {error}
                </div>
            )}

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
                            <SelectContent className="bg-white">
                                <SelectItem value="all">All Status</SelectItem>
                                <SelectItem value="completed">Completed</SelectItem>
                                <SelectItem value="in-progress">In Progress</SelectItem>
                                <SelectItem value="failed">Failed</SelectItem>
                                <SelectItem value="pending">Pending</SelectItem>
                            </SelectContent>
                        </Select>
                        <div className="relative flex-1 max-w-sm">
                            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search steps or sources..."
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
                    <CardTitle>Event-Driven Pipeline Flow</CardTitle>
                    <CardDescription>Real-time monitoring of CTI data processing pipeline</CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                    <div className="relative overflow-x-auto w-full">
                        {loading ? (
                            <div className="flex justify-center items-center py-20">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-600" />
                                <span className="ml-3">Loading pipeline data...</span>
                            </div>
                        ) : (
                            <div className="relative w-full">
                                <div className="relative z-10 flex items-center justify-evenly px-7 py-7 gap-7" style={{ minHeight: "650px", minWidth: "max-content" }}>
                                    {/* Event Monitoring Sources */}
                                    <div className="flex flex-col justify-center flex-shrink-0" style={{ width: "280px" }}>
                                        <div className="w-full bg-gradient-to-br from-amber-50 to-orange-100 border border-amber-200 rounded-lg p-4" style={{ minHeight: "450px" }}>
                                            <div className="mb-4">
                                                <h3 className="text-sm font-medium flex items-center gap-2">
                                                    <Database className="h-4 w-4 text-amber-600" />
                                                    Event Monitoring
                                                </h3>
                                                <div className="text-sm text-muted-foreground mt-2">
                                                    {eventSources.filter(s => s.can_trigger).length} ready sources
                                                </div>
                                            </div>
                                            <div className="space-y-2">{eventSources.map((source) => (
                                                <div key={source.name} className="space-y-2">
                                                    <button
                                                        className={`w-full flex items-center justify-between h-11 text-sm px-3 py-2 rounded border transition-colors ${getStatusColor(source.status).replace('text-', 'hover:text-').replace('bg-', 'hover:bg-')}`}
                                                        onClick={() => setShowEventDetails(prev => ({
                                                            ...prev,
                                                            [source.name]: !prev[source.name]
                                                        }))}
                                                    >
                                                        <span className="flex items-center gap-1 truncate">
                                                            {getStatusIcon(source.status)}
                                                            <span className="font-medium truncate">{source.name.toUpperCase()}</span>
                                                        </span>
                                                        <ChevronDown className={`h-3 w-3 transition-transform flex-shrink-0 ${showEventDetails[source.name] ? 'rotate-180' : ''}`} />
                                                    </button>
                                                    {showEventDetails[source.name] && (
                                                        <div className="ml-2 p-2 bg-white/50 rounded border text-xs space-y-1">
                                                            <div>Status: <span className={`px-1 rounded ${getStatusColor(source.status)}`}>{source.status}</span></div>
                                                            <div>Last trigger: {formatLastRun(source.last_trigger)}</div>
                                                            {source.cooldown_remaining_minutes && (
                                                                <div>Cooldown: {Math.round(source.cooldown_remaining_minutes)}m</div>
                                                            )}
                                                            <button
                                                                onClick={() => handleTriggerEventSource(source.name)}
                                                                disabled={!source.can_trigger}
                                                                className={`w-full mt-2 px-2 py-1 rounded text-xs flex items-center justify-center gap-1 ${source.can_trigger
                                                                    ? 'bg-blue-100 hover:bg-blue-200 text-blue-800'
                                                                    : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                                                                    }`}
                                                            >
                                                                <Zap className="h-3 w-3" /> Trigger
                                                            </button>
                                                        </div>
                                                    )}
                                                </div>
                                            ))}
                                            </div>
                                        </div>
                                    </div>

                                    {/* CTI Ingestion Steps */}
                                    <div className="flex flex-col justify-center space-y-3 flex-shrink-0" style={{ width: "220px" }}>
                                        <div className="flex flex-col justify-center space-y-3">
                                            {ingestionSteps.map((step) => (
                                                <div key={step.id} className="w-full h-36 bg-card border border-border rounded-lg hover:shadow-md transition-shadow p-3">
                                                    <div className="flex items-center justify-between mb-2">
                                                        <h4 className="text-sm font-medium">{step.source?.toUpperCase()}</h4>
                                                        {getStatusIcon(step.status)}
                                                    </div>
                                                    <div className={`text-sm px-2 py-1 rounded border ${getStatusColor(step.status)} mb-2`}>
                                                        {step.status}
                                                    </div>
                                                    <div className="text-sm text-muted-foreground mb-2">
                                                        Last: {formatLastRun(step.lastRun)}
                                                    </div>
                                                    <button
                                                        onClick={() => handleTriggerDAG(step.dagId)}
                                                        className="w-full text-sm px-2 py-1 border border-border rounded hover:bg-muted flex items-center justify-center gap-1"
                                                    >
                                                        <Play className="h-3 w-3" />
                                                        Run DAG
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Preprocess Step */}
                                    {preprocessStep && (
                                        <div className="flex flex-col justify-center flex-shrink-0" style={{ width: "300px" }}>
                                            <div className="w-full bg-card border border-border rounded-lg hover:shadow-lg transition-shadow p-4" style={{ minHeight: "450px" }}>
                                                <div className="flex items-center justify-between mb-3">
                                                    <h4 className="text-sm font-medium">{preprocessStep.name}</h4>
                                                    {getStatusIcon(preprocessStep.status)}
                                                </div>
                                                <div className={`text-sm px-2 py-1 rounded border ${getStatusColor(preprocessStep.status)} mb-3`}>
                                                    {preprocessStep.status}
                                                </div>
                                                <div className="text-sm text-muted-foreground mb-3">
                                                    Last run: {formatLastRun(preprocessStep.lastRun)}
                                                </div>
                                                <button
                                                    onClick={() => handleTriggerDAG(preprocessStep.dagId)}
                                                    className="w-full px-3 py-1 border border-border rounded hover:bg-muted flex items-center justify-center gap-2 text-sm mb-3"
                                                >
                                                    <Play className="h-3 w-3" />
                                                    Trigger DAG
                                                </button>
                                                <div className="text-sm text-muted-foreground">
                                                    <div className="font-medium mb-2 flex items-center gap-1">
                                                        <Users className="h-3 w-3" />
                                                        Tasks ({preprocessTasks.length})
                                                    </div>
                                                    <div className="space-y-1">
                                                        {preprocessTasks.map((task) => (
                                                            <div key={task.task_id} className="flex items-center justify-between p-2 bg-muted/30 rounded">
                                                                <span className="text-sm">{task.task_id}</span>
                                                                <div className="ml-2 flex-shrink-0">
                                                                    {getStatusIcon(task.state || "pending")}
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* LLM and RAG */}
                                    <div className="flex flex-col justify-center space-y-4 flex-shrink-0" style={{ width: "220px" }}>
                                        <div className="flex flex-col justify-center space-y-4">
                                            {llmStep && (
                                                <div className="w-full h-32 bg-card border border-border rounded-lg hover:shadow-md transition-shadow p-3">
                                                    <div className="flex items-center justify-between mb-2">
                                                        <h4 className="text-sm font-medium">LLM Mapping</h4>
                                                        {getStatusIcon(llmStep.status)}
                                                    </div>
                                                    <div className={`text-sm px-2 py-1 rounded border ${getStatusColor(llmStep.status)} mb-2`}>
                                                        {llmStep.status}
                                                    </div>
                                                    <button
                                                        onClick={() => handleTriggerDAG(llmStep.dagId)}
                                                        className="w-full text-sm px-2 py-1 border border-border rounded hover:bg-muted flex items-center justify-center gap-1"
                                                    >
                                                        <Play className="h-3 w-3" />
                                                        Trigger
                                                    </button>
                                                </div>
                                            )}
                                            {ragStep && (
                                                <div className="w-full h-32 bg-card border border-border rounded-lg hover:shadow-md transition-shadow p-3">
                                                    <div className="flex items-center justify-between mb-2">
                                                        <h4 className="text-sm font-medium">RAG Search</h4>
                                                        {getStatusIcon(ragStep.status)}
                                                    </div>
                                                    <div className={`text-sm px-2 py-1 rounded border ${getStatusColor(ragStep.status)} mb-2`}>
                                                        {ragStep.status}
                                                    </div>
                                                    <button
                                                        onClick={() => handleTriggerDAG(ragStep.dagId)}
                                                        className="w-full text-sm px-2 py-1 border border-border rounded hover:bg-muted flex items-center justify-center gap-1"
                                                    >
                                                        <Play className="h-3 w-3" />
                                                        Trigger
                                                    </button>
                                                </div>
                                            )}
                                        </div>
                                    </div>

                                    {/* LLM-as-a-judge */}
                                    {judgeStep && (
                                        <div className="flex flex-col justify-center flex-shrink-0" style={{ width: "220px" }}>
                                            <div className="w-full bg-card border border-border rounded-lg hover:shadow-lg transition-shadow p-4" style={{ minHeight: "150px" }}>
                                                <div className="flex items-center justify-between mb-3">
                                                    <h4 className="text-sm font-medium">LLM Judge</h4>
                                                    {getStatusIcon(judgeStep.status)}
                                                </div>
                                                <div className="space-y-2">
                                                    <div className={`text-sm px-2 py-1 rounded border ${getStatusColor(judgeStep.status)}`}>
                                                        {judgeStep.status}
                                                    </div>
                                                    <button
                                                        onClick={() => handleTriggerDAG(judgeStep.dagId)}
                                                        className="w-full px-3 py-1 border border-border rounded hover:bg-muted flex items-center justify-center gap-1 text-sm"
                                                    >
                                                        <Play className="h-3 w-3" />
                                                        Trigger
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>

                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}