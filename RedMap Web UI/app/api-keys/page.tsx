"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Key, Plus, Copy, Eye, EyeOff, Trash2, Shield } from "lucide-react"
import { useState } from "react"

export default function ApiKeysPage() {
  const [showKeys, setShowKeys] = useState<{ [key: string]: boolean }>({})
  const [newKeyName, setNewKeyName] = useState("")

  const apiKeys = [
    {
      id: "1",
      name: "Production API Key",
      key: "rmp_sk_1234567890abcdef1234567890abcdef",
      created: "2024-01-15",
      lastUsed: "2 hours ago",
      permissions: ["read", "write"],
      status: "active",
    },
    {
      id: "2",
      name: "Development Key",
      key: "rmp_sk_abcdef1234567890abcdef1234567890",
      created: "2024-01-10",
      lastUsed: "1 day ago",
      permissions: ["read"],
      status: "active",
    },
    {
      id: "3",
      name: "Integration Testing",
      key: "rmp_sk_fedcba0987654321fedcba0987654321",
      created: "2024-01-05",
      lastUsed: "Never",
      permissions: ["read", "write"],
      status: "inactive",
    },
  ]

  const toggleKeyVisibility = (keyId: string) => {
    setShowKeys((prev) => ({
      ...prev,
      [keyId]: !prev[keyId],
    }))
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    // You could add a toast notification here
  }

  const maskKey = (key: string) => {
    return key.substring(0, 12) + "..." + key.substring(key.length - 4)
  }

  return (
    <div className="w-full px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Key className="h-8 w-8 text-yellow-600" />
          API Keys
        </h1>
        <p className="text-muted-foreground">Manage your RedMap API keys for secure integration access</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Create New Key */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5" />
              Create New Key
            </CardTitle>
            <CardDescription>Generate a new API key for your applications</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="key-name">Key Name</Label>
              <Input
                id="key-name"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="e.g., Production API Key"
              />
            </div>

            <div className="space-y-2">
              <Label>Permissions</Label>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <input type="checkbox" id="read" className="rounded" defaultChecked />
                  <Label htmlFor="read">Read Access</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <input type="checkbox" id="write" className="rounded" />
                  <Label htmlFor="write">Write Access</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <input type="checkbox" id="admin" className="rounded" />
                  <Label htmlFor="admin">Admin Access</Label>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label>API Format</Label>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <input type="radio" id="sigma" name="format" className="rounded" defaultChecked />
                  <Label htmlFor="sigma">Sigma Rules</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <input type="radio" id="kql" name="format" className="rounded" />
                  <Label htmlFor="kql">KQL (Kusto Query Language)</Label>
                </div>
                <div className="flex items-center space-x-2">
                  <input type="radio" id="stix" name="format" className="rounded" />
                  <Label htmlFor="stix">STIX Format</Label>
                </div>
              </div>
            </div>

            <Button className="w-full">
              <Plus className="h-4 w-4 mr-2" />
              Generate API Key
            </Button>
          </CardContent>
        </Card>

        {/* API Keys List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Your API Keys</CardTitle>
            <CardDescription>Manage and monitor your existing API keys</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {apiKeys.map((apiKey) => (
                <div key={apiKey.id} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <Shield className="h-5 w-5 text-blue-500" />
                      <div>
                        <p className="font-medium">{apiKey.name}</p>
                        <p className="text-sm text-muted-foreground">
                          Created: {apiKey.created} • Last used: {apiKey.lastUsed}
                        </p>
                      </div>
                    </div>
                    <Badge variant={apiKey.status === "active" ? "default" : "secondary"}>{apiKey.status}</Badge>
                  </div>

                  <div className="flex items-center space-x-2 mb-3">
                    <Input
                      value={showKeys[apiKey.id] ? apiKey.key : maskKey(apiKey.key)}
                      readOnly
                      className="font-mono text-sm"
                    />
                    <Button variant="ghost" size="sm" onClick={() => toggleKeyVisibility(apiKey.id)}>
                      {showKeys[apiKey.id] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => copyToClipboard(apiKey.key)}>
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex space-x-1">
                      {apiKey.permissions.map((permission) => (
                        <Badge key={permission} variant="outline" className="text-xs">
                          {permission}
                        </Badge>
                      ))}
                    </div>
                    <Button variant="ghost" size="sm" className="text-red-600 hover:text-red-700">
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Usage Guidelines */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>API Usage Guidelines</CardTitle>
          <CardDescription>Important information about using RedMap API keys</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <h4 className="font-medium">Authentication</h4>
              <p className="text-sm text-muted-foreground">Include your API key in the Authorization header:</p>
              <code className="block p-2 bg-muted rounded text-sm">Authorization: Bearer rmp_sk_your_api_key_here</code>
            </div>

            <div className="space-y-2">
              <h4 className="font-medium">Rate Limits</h4>
              <p className="text-sm text-muted-foreground">API requests are limited to:</p>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• 1000 requests per hour</li>
                <li>• 10,000 requests per day</li>
                <li>• Burst limit: 100 requests per minute</li>
              </ul>
            </div>
          </div>

          <div className="pt-4 border-t">
            <h4 className="font-medium mb-2">Security Best Practices</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Never expose API keys in client-side code or public repositories</li>
              <li>• Rotate keys regularly and immediately revoke compromised keys</li>
              <li>• Use environment variables to store API keys in your applications</li>
              <li>• Monitor API key usage and set up alerts for unusual activity</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
