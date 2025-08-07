"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Workflow, Search, Filter, AlertCircle, CheckCircle, Clock, Activity, ChevronDown, ChevronUp } from "lucide-react"
import { useState, useEffect, useMemo, useCallback } from "react"
import axios from "axios"
import React from "react"

interface Log {
  id: string
  timestamp: string
  workflow: string
  type: string
  message: string
  source: string
  status: string
  startDate?: string
  endDate?: string
  duration?: string
}

const INITIAL_LIMIT = 20

const N8nPage = React.memo(() => {
  const [searchTerm, setSearchTerm] = useState("")
  const [logs, setLogs] = useState<Log[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set())
  const [limit, setLimit] = useState(INITIAL_LIMIT)
  const [logsToday, setLogsToday] = useState(0)

  const fetchWorkflows = useCallback(async () => {
    setLoading(true)
    try {
      const [workflowsResponse, executionsResponse] = await Promise.all([
        axios.get('/api/n8n/workflows'),
        axios.get('/api/n8n/executions', { params: { limit, offset: 0, includeData: true } }),
      ])
      const workflows = workflowsResponse.data.data || []
      const executions = executionsResponse.data.data?.results || executionsResponse.data.data || []

      const generatedLogs = executions.map((execution: any) => {
        const workflow = workflows.find((w: any) => w.id === execution.workflowId) || { name: execution.workflowName || `Workflow ${execution.workflowId}` }
        const executionStatus = execution.status || 'success'
        const isError = executionStatus === 'error' || !execution.finished

        const startDate = execution.startedAt ? new Date(execution.startedAt).toLocaleString() : 'Unknown'
        const endDate = execution.stoppedAt ? new Date(execution.stoppedAt).toLocaleString() : execution.finished ? 'Unknown' : 'In progress'
        const duration = execution.startedAt && execution.stoppedAt
          ? (() => {
            const durationMs = new Date(execution.stoppedAt).getTime() - new Date(execution.startedAt).getTime()
            return durationMs >= 60000 ? `${Math.round(durationMs / 60000)}min` : `${Math.round(durationMs / 1000)}s`
          })()
          : execution.finished ? 'Unknown' : 'In progress'

        return {
          id: execution.id || String(Math.random()), // Fallback if id missing
          timestamp: execution.stoppedAt || execution.startedAt || new Date().toISOString(),
          workflow: workflow.name,
          type: isError ? 'incident' : 'log',
          message: isError ? `Error in ${workflow.name}` : `Execution ${executionStatus} for ${workflow.name}`,
          source: 'n8n Workflow',
          status: execution.finished ? 'completed' : 'investigating',
          startDate,
          endDate,
          duration,
        }
      })

      setLogs(generatedLogs)

      const today = new Date()
      const todayLogsCount = generatedLogs.filter((log: Log) => new Date(log.timestamp).toDateString() === today.toDateString()).length
      setLogsToday(todayLogsCount)

      setError(null)
    } catch (err: any) {
      setError(`Failed to fetch n8n data: ${err.response?.data?.message || err.message}`)
    } finally {
      setLoading(false)
    }
  }, [limit])

  useEffect(() => {
    fetchWorkflows()
    const interval = setInterval(fetchWorkflows, 60000) // Increased to 60s
    return () => clearInterval(interval)
  }, [fetchWorkflows])

  const loadMore = useCallback(() => {
    setLimit(prev => prev + INITIAL_LIMIT)
  }, [])

  const toggleLogDetails = useCallback((logId: string) => {
    setExpandedLogs(prev => {
      const newSet = new Set(prev)
      if (newSet.has(logId)) newSet.delete(logId)
      else newSet.add(logId)
      return newSet
    })
  }, [])

  const filteredLogs = useMemo(() => {
    return logs.filter((log) =>
      log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.workflow.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [logs, searchTerm])

  const metrics = useMemo(() => ({
    activeWorkflows: new Set(logs.map(log => log.workflow)).size,
    openIncidents: logs.filter(log => log.status === 'investigating').length,
    successRate: logs.length > 0 ? ((logs.filter(log => log.status === 'completed').length / logs.length) * 100).toFixed(1) : 'N/A',
  }), [logs])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "investigating": return <Clock className="h-4 w-4 text-yellow-500" />
      case "completed": return <CheckCircle className="h-4 w-4 text-blue-500" />
      default: return <Activity className="h-4 w-4" />
    }
  }

  return (
    <div className="w-full px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Workflow className="h-8 w-8 text-blue-600" />
          n8n Monitoring
        </h1>
        <p className="text-muted-foreground">Monitor security logs and incidents from n8n workflows</p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 text-red-700 border border-red-200 rounded-lg">
          {error}
        </div>
      )}

      {loading ? (
        <div className="grid gap-6 md:grid-cols-4 mb-6">
          {[...Array(4)].map((_, index) => (
            <Card key={index} className="animate-pulse">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="h-4 w-20 bg-gray-300 rounded" />
                <div className="h-4 w-4 bg-gray-300 rounded" />
              </CardHeader>
              <CardContent>
                <div className="h-6 w-16 bg-gray-300 rounded mb-2" />
                <div className="h-4 w-24 bg-gray-300 rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-4 mb-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Workflows</CardTitle>
              <Workflow className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.activeWorkflows}</div>
              <p className="text-xs text-muted-foreground">Running workflows</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Open Incidents</CardTitle>
              <AlertCircle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.openIncidents}</div>
              <p className="text-xs text-muted-foreground">Require attention</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Logs Today</CardTitle>
              <Activity className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{logsToday}</div>
              <p className="text-xs text-muted-foreground">Security events</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
              <CheckCircle className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.successRate}%</div>
              <p className="text-xs text-muted-foreground">Workflow execution</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4" />
              <span className="text-sm font-medium">Filters:</span>
            </div>
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search logs and incidents..."
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
          <CardTitle>Security Logs & Incidents</CardTitle>
          <CardDescription>Real-time monitoring of security events from n8n workflows</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredLogs.slice(0, limit).map((log) => {
              const isExpanded = expandedLogs.has(log.id)
              return (
                <div
                  key={log.id}
                  className="border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-start justify-between p-4">
                    <div className="flex items-start space-x-4 flex-1">
                      {getStatusIcon(log.status)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <p className="font-medium truncate">{log.message}</p>
                        </div>
                        <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                          <span>{log.timestamp}</span>
                          <span>•</span>
                          <span>{log.workflow}</span>
                          <span>•</span>
                          <span>{log.source}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 ml-4">
                      <Badge variant="outline" className="capitalize">
                        {log.status}
                      </Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => toggleLogDetails(log.id)}
                        className="flex items-center gap-1"
                      >
                        View Details
                        {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                      </Button>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="px-4 pb-4 border-t bg-muted/20">
                      <div className="pt-4 grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-muted-foreground">Start Date:</span>
                          <p className="mt-1">{log.startDate}</p>
                        </div>
                        <div>
                          <span className="font-medium text-muted-foreground">End Date:</span>
                          <p className="mt-1">{log.endDate}</p>
                        </div>
                        <div>
                          <span className="font-medium text-muted-foreground">Duration:</span>
                          <p className="mt-1">{log.duration}</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
            {limit < logs.length && (
              <div className="text-center">
                <Button onClick={loadMore} variant="outline" className="mt-4">
                  Load More
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
})

N8nPage.displayName = "N8nPage"

export default N8nPage