"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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
    Activity,
    Clock,
} from "lucide-react"
import { useState, useEffect, useCallback } from "react"
import axios from "axios"

interface PipelineStep {
    id: string
    name: string
    status: "completed" | "in-progress" | "failed" | "pending"
    dagId?: string
    source?: string
    nextSteps?: string[]
}

export default function FullPipelinePage() {
    const [steps, setSteps] = useState<PipelineStep[]>([])
    const [error, setError] = useState<string | null>(null)
    const [loading, setLoading] = useState(true)
    const [searchTerm, setSearchTerm] = useState("")
    const [statusFilter, setStatusFilter] = useState("all")

    const AIRFLOW_API_URL = "/api/airflow"
    const authHeader = { headers: { "Content-Type": "application/json" } }

    const fetchPipelineData = useCallback(async () => {
        setLoading(true)
        try {
            const dagsResponse = await axios.get(`${AIRFLOW_API_URL}/dags`, authHeader)
            const dagList = dagsResponse.data.dags || []

            // Détecter les DAGs d'ingestion
            const ingestionDags = dagList.filter((dag: { dag_id: string }) => dag.dag_id.startsWith("cti_pipeline_"))
            const sources = ingestionDags.map((dag: { dag_id: string }) => dag.dag_id.replace("cti_pipeline_", ""))

            // Définir les étapes avec mappage dynamique
            const pipelineSteps: PipelineStep[] = [
                ...sources.map((source: string) => ({
                    id: `cti-ingestion-${source}`,
                    name: `CTI Ingestion (${source})`,
                    status: ingestionDags.find((dag: { dag_id: string; is_paused: boolean }) => dag.dag_id === `cti_pipeline_${source}`)?.is_paused ? "pending" : "in-progress",
                    dagId: `cti_pipeline_${source}`,
                    source,
                    nextSteps: ["preprocess_pipeline"],
                })),
                {
                    id: "preprocess_pipeline",
                    name: "Preprocess",
                    status: "in-progress",
                    dagId: "preprocess_pipeline.py",
                    nextSteps: ["llm-mitre-mapping", "retrieval"],
                },
                {
                    id: "llm-mitre-mapping",
                    name: "LLM mitre mapping",
                    status: "completed",
                    dagId: "llm_mitre_mapping_dag.py",
                    nextSteps: ["llm-as-judge"],
                },
                {
                    id: "retrieval",
                    name: "Retrieval",
                    status: "pending",
                    dagId: "rag_dag.py",
                    nextSteps: ["augmented-search"],
                },
                {
                    id: "augmented-search",
                    name: "Augmented Search",
                    status: "failed",
                    dagId: "test_dag.py",
                    nextSteps: ["llm-as-judge"],
                },
                {
                    id: "llm-as-judge",
                    name: "LLM-as-judge",
                    status: "pending",
                    dagId: "llm_judge_dag.py",
                },
            ]

            setSteps(pipelineSteps)
            setError(null)
        } catch (err: any) {
            setError(`Failed to fetch pipeline data: ${err.response?.data?.message || err.message}`)
        } finally {
            setLoading(false)
        }
    }, [])

    useEffect(() => {
        fetchPipelineData()
        const interval = setInterval(fetchPipelineData, 30000)
        return () => clearInterval(interval)
    }, [fetchPipelineData])

    const getStatusColor = (status: string) => {
        switch (status) {
            case "completed": return "default"
            case "in-progress": return "secondary"
            case "failed": return "destructive"
            case "pending": return "outline"
            default: return "outline"
        }
    }

    const getStatusIcon = (status: string) => {
        switch (status) {
            case "completed": return <CheckCircle className="h-4 w-4 text-green-500" />
            case "in-progress": return <Activity className="h-4 w-4 text-yellow-500" />
            case "failed": return <AlertCircle className="h-4 w-4 text-red-500" />
            case "pending": return <Clock className="h-4 w-4" />
            default: return <Clock className="h-4 w-4" />
        }
    }

    const handleTriggerStep = async (dagId: string | undefined) => {
        if (!dagId) return
        try {
            await axios.post(`${AIRFLOW_API_URL}/dags/${dagId}/dagRuns`, { conf: {} }, authHeader)
            console.log(`Triggered DAG: ${dagId}`)
            fetchPipelineData()
        } catch (err: any) {
            setError(`Failed to trigger DAG ${dagId}: ${err.response?.data?.error || err.message}`)
        }
    }

    const filteredSteps = steps.filter(step =>
        step.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (step.source?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false)
    ).filter(step => statusFilter === "all" || step.status === statusFilter)

    return (
        <div className="w-full px-4 py-8">
            <div className="mb-8">
                <h1 className="text-3xl font-bold flex items-center gap-3">
                    <Wind className="h-8 w-8 text-cyan-600" />
                    Full Pipeline Monitoring
                </h1>
                <p className="text-muted-foreground">End-to-end view of security data pipeline process</p>
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
                            <SelectContent>
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
                    <CardTitle>Pipeline Process Flow</CardTitle>
                    <CardDescription>Interactive view of the full pipeline stages</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="relative">
                        {loading ? (
                            <div className="flex justify-center">
                                <div className="animate-pulse bg-gray-300 h-8 w-8 rounded-full" />
                            </div>
                        ) : (
                            <div className="grid grid-cols-2 gap-4">
                                {/* Colonne pour les étapes d'ingestion (verticale) */}
                                <div className="flex flex-col space-y-4">
                                    {filteredSteps.filter(step => step.id.startsWith("cti-ingestion-")).map((step, index) => (
                                        <div key={step.id} className="relative">
                                            <Card className="w-40 h-32">
                                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                                    <CardTitle className="text-xs font-medium">{step.name}</CardTitle>
                                                    {getStatusIcon(step.status)}
                                                </CardHeader>
                                                <CardContent>
                                                    <Badge variant={getStatusColor(step.status)} className="text-xs">{step.status}</Badge>
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => handleTriggerStep(step.dagId)}
                                                        className="mt-1 w-full text-xs"
                                                        disabled={!step.dagId}
                                                    >
                                                        <Play className="h-3 w-3 mr-1" /> Trigger
                                                    </Button>
                                                </CardContent>
                                            </Card>
                                            {index === filteredSteps.filter(step => step.id.startsWith("cti-ingestion-")).length - 1 && (
                                                <svg
                                                    className="absolute w-16 h-16"
                                                    style={{ top: "100%", left: "50%", transform: "translateX(-50%)" }}
                                                >
                                                    <line
                                                        x1="50%"
                                                        y1="0%"
                                                        x2="50%"
                                                        y2="100%"
                                                        stroke={filteredSteps.find(step => step.id === "preprocess_pipeline")?.status === "completed" ? "green" : filteredSteps.find(step => step.id === "preprocess_pipeline")?.status === "in-progress" ? "orange" : "black"}
                                                        strokeWidth="2"
                                                    />
                                                </svg>
                                            )}
                                        </div>
                                    ))}
                                </div>
                                {/* Colonne pour les autres étapes (verticale à côté) */}
                                <div className="flex flex-col space-y-4">
                                    {filteredSteps.filter(step => !step.id.startsWith("cti-ingestion-")).map((step, index, filteredNonIngestion) => (
                                        <div key={step.id} className="relative">
                                            <Card className="w-full">
                                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                                    <CardTitle className="text-sm font-medium">{step.name}</CardTitle>
                                                    {getStatusIcon(step.status)}
                                                </CardHeader>
                                                <CardContent>
                                                    <Badge variant={getStatusColor(step.status)}>{step.status}</Badge>
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => handleTriggerStep(step.dagId)}
                                                        className="mt-2 w-full"
                                                        disabled={!step.dagId}
                                                    >
                                                        <Play className="h-4 w-4 mr-1" /> Trigger
                                                    </Button>
                                                </CardContent>
                                            </Card>
                                            {index < filteredNonIngestion.length - 1 && (
                                                <svg
                                                    className="absolute w-16 h-16"
                                                    style={{ top: "100%", left: "50%", transform: "translateX(-50%)" }}
                                                >
                                                    <line
                                                        x1="50%"
                                                        y1="0%"
                                                        x2="50%"
                                                        y2="100%"
                                                        stroke={filteredNonIngestion[index + 1].status === "completed" ? "green" : filteredNonIngestion[index + 1].status === "in-progress" ? "orange" : "black"}
                                                        strokeWidth="2"
                                                    />
                                                </svg>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}