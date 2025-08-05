"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Shield, AlertTriangle, CheckCircle, Activity, TrendingUp, Clock, Filter, Search } from "lucide-react"
import {
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Legend,
} from "recharts"
import { useState } from "react"

const threatData = [
  { time: "00:00", threats: 12, resolved: 8 },
  { time: "04:00", threats: 19, resolved: 15 },
  { time: "08:00", threats: 35, resolved: 28 },
  { time: "12:00", threats: 42, resolved: 38 },
  { time: "16:00", threats: 28, resolved: 25 },
  { time: "20:00", threats: 23, resolved: 20 },
]

const severityData = [
  { name: "Critical", value: 8, color: "#dc2626" },
  { name: "High", value: 15, color: "#ea580c" },
  { name: "Medium", value: 32, color: "#ca8a04" },
  { name: "Low", value: 45, color: "#16a34a" },
]

const incidentTypes = [
  { type: "Malware", count: 23, trend: "+12%" },
  { type: "Phishing", count: 18, trend: "-5%" },
  { type: "DDoS", count: 12, trend: "+8%" },
  { type: "Data Breach", count: 7, trend: "+15%" },
  { type: "Insider Threat", count: 4, trend: "-2%" },
]

export default function DashboardPage() {
  const [timeFilter, setTimeFilter] = useState("24h")
  const [severityFilter, setSeverityFilter] = useState("all")
  const [searchTerm, setSearchTerm] = useState("")

  return (
    <div className="w-full px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Security Dashboard</h1>
        <p className="text-muted-foreground">Monitor your security posture with AI-powered analytics</p>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4" />
              <span className="text-sm font-medium">Filters:</span>
            </div>

            <Select value={timeFilter} onValueChange={setTimeFilter}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1h">Last Hour</SelectItem>
                <SelectItem value="24h">Last 24h</SelectItem>
                <SelectItem value="7d">Last 7 days</SelectItem>
                <SelectItem value="30d">Last 30 days</SelectItem>
              </SelectContent>
            </Select>

            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severity</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>

            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search incidents..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Threats</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">23</div>
            <p className="text-xs text-muted-foreground">+2 from last hour</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resolved Issues</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">1,247</div>
            <p className="text-xs text-muted-foreground">+18% from last week</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">AI Detection Rate</CardTitle>
            <Activity className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">98.5%</div>
            <p className="text-xs text-muted-foreground">AI-powered accuracy</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Response Time</CardTitle>
            <Clock className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">2.3m</div>
            <p className="text-xs text-muted-foreground">Average response</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2 mb-8">
        {/* Threat Timeline */}
        <Card>
          <CardHeader>
            <CardTitle>Threat Detection Timeline</CardTitle>
            <CardDescription>Real-time threat detection and resolution</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer
              config={{
                threats: { label: "Threats Detected", color: "hsl(var(--chart-1))" },
                resolved: { label: "Threats Resolved", color: "hsl(var(--chart-2))" },
              }}
              className="h-[300px]"
            >
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={threatData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Area
                    type="monotone"
                    dataKey="threats"
                    stackId="1"
                    stroke="var(--color-threats)"
                    fill="var(--color-threats)"
                    fillOpacity={0.6}
                  />
                  <Area
                    type="monotone"
                    dataKey="resolved"
                    stackId="1"
                    stroke="var(--color-resolved)"
                    fill="var(--color-resolved)"
                    fillOpacity={0.6}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>

        {/* Severity Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Threat Severity Distribution</CardTitle>
            <CardDescription>Current threat landscape by severity</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer
              config={{
                critical: { label: "Critical", color: "#dc2626" },
                high: { label: "High", color: "#ea580c" },
                medium: { label: "Medium", color: "#ca8a04" },
                low: { label: "Low", color: "#16a34a" },
              }}
              className="h-[300px]"
            >
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={severityData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {severityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <ChartTooltip content={<ChartTooltipContent />} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Incident Types */}
        <Card>
          <CardHeader>
            <CardTitle>Top Incident Types</CardTitle>
            <CardDescription>Most common security incidents detected</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {incidentTypes.map((incident, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 rounded-full bg-red-500"></div>
                    <div>
                      <p className="font-medium">{incident.type}</p>
                      <p className="text-sm text-muted-foreground">{incident.count} incidents</p>
                    </div>
                  </div>
                  <Badge variant={incident.trend.startsWith("+") ? "destructive" : "default"}>{incident.trend}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* AI Insights */}
        <Card>
          <CardHeader>
            <CardTitle>AI Security Insights</CardTitle>
            <CardDescription>Latest AI-powered security recommendations</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-3 border rounded-lg bg-blue-50 dark:bg-blue-950">
              <div className="flex items-center space-x-2 mb-2">
                <Activity className="h-4 w-4 text-blue-600" />
                <span className="font-medium text-blue-900 dark:text-blue-100">Pattern Detected</span>
              </div>
              <p className="text-sm text-blue-800 dark:text-blue-200">
                AI detected unusual login patterns from Eastern Europe. Consider implementing geo-blocking.
              </p>
            </div>

            <div className="p-3 border rounded-lg bg-yellow-50 dark:bg-yellow-950">
              <div className="flex items-center space-x-2 mb-2">
                <TrendingUp className="h-4 w-4 text-yellow-600" />
                <span className="font-medium text-yellow-900 dark:text-yellow-100">Trend Analysis</span>
              </div>
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                Phishing attempts decreased by 15% after implementing new email filters.
              </p>
            </div>

            <div className="p-3 border rounded-lg bg-green-50 dark:bg-green-950">
              <div className="flex items-center space-x-2 mb-2">
                <Shield className="h-4 w-4 text-green-600" />
                <span className="font-medium text-green-900 dark:text-green-100">Recommendation</span>
              </div>
              <p className="text-sm text-green-800 dark:text-green-200">
                Update firewall rules to block 3 new malicious IP ranges identified by AI.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
