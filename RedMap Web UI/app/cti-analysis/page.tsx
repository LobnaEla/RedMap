"use client"

import type React from "react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { FileText, Upload, Brain, Shield, AlertTriangle, CheckCircle, Clock, Download } from "lucide-react"
import { useState } from "react"

export default function CTIAnalysisPage() {
  const [file, setFile] = useState<File | null>(null)
  const [analysisResult, setAnalysisResult] = useState<any>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = event.target.files?.[0]
    if (uploadedFile) {
      setFile(uploadedFile)
      setAnalysisResult(null)
    }
  }

  const handleAnalyze = async () => {
    if (!file) return

    setIsAnalyzing(true)
    setAnalysisProgress(0)

    // Simulate analysis progress
    const progressInterval = setInterval(() => {
      setAnalysisProgress((prev) => {
        if (prev >= 100) {
          clearInterval(progressInterval)
          return 100
        }
        return prev + 10
      })
    }, 200)

    // Simulate API call
    setTimeout(() => {
      setIsAnalyzing(false)
      setAnalysisResult({
        fileName: file.name,
        fileSize: `${(file.size / 1024).toFixed(2)} KB`,
        analysisTime: "2.3 seconds",
        threatLevel: "Medium",
        confidence: 87,
        indicators: [
          { type: "IP Address", value: "192.168.1.100", threat: "High", description: "Known malicious IP" },
          { type: "Domain", value: "malicious-site.com", threat: "Critical", description: "C&C server domain" },
          { type: "Hash", value: "a1b2c3d4e5f6...", threat: "Medium", description: "Suspicious file hash" },
          { type: "Email", value: "phishing@evil.com", threat: "High", description: "Phishing campaign source" },
        ],
        aiInsights: [
          "This file contains indicators associated with the APT29 threat group",
          "Pattern analysis suggests this is part of a spear-phishing campaign",
          "Recommended action: Block all associated IPs and domains immediately",
          "Similar patterns detected in 3 other recent incidents",
        ],
        recommendations: [
          "Update firewall rules to block identified IP addresses",
          "Add domains to DNS blacklist",
          "Scan network for similar file hashes",
          "Alert security team about potential APT29 activity",
        ],
      })
    }, 2000)
  }

  const getThreatColor = (threat: string) => {
    switch (threat.toLowerCase()) {
      case "critical":
        return "destructive"
      case "high":
        return "destructive"
      case "medium":
        return "secondary"
      case "low":
        return "outline"
      default:
        return "outline"
    }
  }

  return (
    <div className="w-full px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Brain className="h-8 w-8 text-purple-600" />
          CTI Analysis
        </h1>
        <p className="text-muted-foreground">Upload cyber threat intelligence files for AI-powered analysis</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Upload Section */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              Upload CTI File
            </CardTitle>
            <CardDescription>Upload threat intelligence files for analysis</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="file-upload">Select File</Label>
              <Input
                id="file-upload"
                type="file"
                accept=".json,.xml,.txt,.csv,.stix"
                onChange={handleFileUpload}
                className="cursor-pointer"
              />
              <p className="text-xs text-muted-foreground">Supported formats: JSON, XML, TXT, CSV, STIX</p>
            </div>

            {file && (
              <div className="p-3 border rounded-lg bg-muted/50">
                <div className="flex items-center space-x-2">
                  <FileText className="h-4 w-4" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(2)} KB</p>
                  </div>
                </div>
              </div>
            )}

            <Button
              onClick={handleAnalyze}
              disabled={!file || isAnalyzing}
              className="w-full bg-red-600 hover:bg-red-700"
            >
              {isAnalyzing ? (
                <>
                  <Clock className="h-4 w-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Brain className="h-4 w-4 mr-2" />
                  Analyze with AI
                </>
              )}
            </Button>

            {isAnalyzing && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Analysis Progress</span>
                  <span>{analysisProgress}%</span>
                </div>
                <Progress value={analysisProgress} className="w-full" />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results Section */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Analysis Results
            </CardTitle>
            <CardDescription>AI-powered threat intelligence analysis</CardDescription>
          </CardHeader>
          <CardContent>
            {!analysisResult ? (
              <div className="text-center py-12">
                <Brain className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Upload a CTI file to see AI analysis results</p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Summary */}
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="text-center p-4 border rounded-lg">
                    <div className="text-2xl font-bold text-red-600">{analysisResult.threatLevel}</div>
                    <p className="text-sm text-muted-foreground">Threat Level</p>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">{analysisResult.confidence}%</div>
                    <p className="text-sm text-muted-foreground">Confidence</p>
                  </div>
                  <div className="text-center p-4 border rounded-lg">
                    <div className="text-2xl font-bold text-green-600">{analysisResult.analysisTime}</div>
                    <p className="text-sm text-muted-foreground">Analysis Time</p>
                  </div>
                </div>

                {/* Threat Indicators */}
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-red-500" />
                    Threat Indicators
                  </h3>
                  <div className="space-y-3">
                    {analysisResult.indicators.map((indicator: any, index: number) => (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-1">
                            <span className="font-medium">{indicator.type}</span>
                            <Badge variant={getThreatColor(indicator.threat)}>{indicator.threat}</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground font-mono">{indicator.value}</p>
                          <p className="text-xs text-muted-foreground">{indicator.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* AI Insights */}
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <Brain className="h-5 w-5 text-purple-500" />
                    AI Insights
                  </h3>
                  <div className="space-y-2">
                    {analysisResult.aiInsights.map((insight: string, index: number) => (
                      <div key={index} className="p-3 border rounded-lg bg-purple-50 dark:bg-purple-950">
                        <p className="text-sm">{insight}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recommendations */}
                <div>
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    Recommendations
                  </h3>
                  <div className="space-y-2">
                    {analysisResult.recommendations.map((rec: string, index: number) => (
                      <div key={index} className="flex items-start space-x-2 p-3 border rounded-lg">
                        <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                        <p className="text-sm">{rec}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Export Options */}
                <div className="flex justify-end space-x-2 pt-4 border-t">
                  <Button variant="outline">
                    <Download className="h-4 w-4 mr-2" />
                    Export Report
                  </Button>
                  <Button className="bg-red-600 hover:bg-red-700">Create Incident</Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
