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
import { useState } from "react"

export default function AirflowPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")

  const dags = [
    {
      id: "security_log_processing",
      name: "Security Log Processing",
      status: "running",
      lastRun: "1 minute ago",
      nextRun: "in 4 minutes",
      schedule: "*/5 * * * *",
      description: "Process and analyze security logs from multiple sources",
      successRate: "98.5%",
    },
    {
      id: "threat_intel_update",
      name: "Threat Intelligence Update",
      status: "success",
      lastRun: "30 minutes ago",
      nextRun: "in 30 minutes",
      schedule: "0 * * * *",
      description: "Update threat intelligence feeds and indicators",
      successRate: "99.2%",
    },
    {
      id: "vulnerability_scan",
      name: "Vulnerability Scanning",
      status: "paused",
      lastRun: "2 hours ago",
      nextRun: "paused",
      schedule: "0 2 * * *",
      description: "Automated vulnerability assessment and reporting",
      successRate: "95.8%",
    },
    {
      id: "incident_response",
      name: "Incident Response Pipeline",
      status: "failed",
      lastRun: "15 minutes ago",
      nextRun: "in 45 minutes",
      schedule: "*/15 * * * *",
      description: "Automated incident detection and response workflows",
      successRate: "92.1%",
    },
    {
      id: "compliance_reporting",
      name: "Compliance Reporting",
      status: "success",
      lastRun: "1 hour ago",
      nextRun: "tomorrow 9:00 AM",
      schedule: "0 9 * * *",
      description: "Generate compliance reports and audit trails",
      successRate: "100%",
    },
  ]

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

  const handleTriggerDag = (dagId: string) => {
    console.log(`Triggering DAG: ${dagId}`)
    // Here you would make an API call to trigger the DAG
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

      {/* Statistics */}
      <div className="grid gap-6 md:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total DAGs</CardTitle>
            <Wind className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">5</div>
            <p className="text-xs text-muted-foreground">2 running, 1 paused, 2 scheduled</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">97.1%</div>
            <p className="text-xs text-muted-foreground">Last 24 hours</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Task Instances</CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,247</div>
            <p className="text-xs text-muted-foreground">Executed today</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Duration</CardTitle>
            <Clock className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">4.2m</div>
            <p className="text-xs text-muted-foreground">Per task execution</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
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

      {/* DAGs List */}
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
                        <span className="flex items-center gap-1">
                          <CheckCircle className="h-3 w-3" />
                          {dag.successRate}
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
