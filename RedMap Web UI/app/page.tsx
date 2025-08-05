import { Button } from "@/components/ui/button"
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Shield, Zap, Lock, BarChart3, Workflow, Key } from "lucide-react"
import Link from "next/link"

export default function HomePage() {
  return (
    <div className="flex flex-col w-full">
      {/* Hero Section */}
      <section className="w-full px-4 py-24 md:py-32">
        <div className="w-full text-center">
          <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
            Advanced Cybersecurity
            <span className="text-red-600"> Analytics Platform</span>
          </h1>
          <p className="mt-6 text-lg leading-8 text-muted-foreground">
            Empower your security operations with RedMap's comprehensive analytics platform. Integrate with n8n and
            Airflow for automated threat detection and response workflows.
          </p>
          <div className="mt-10 flex items-center justify-center gap-x-6">
            <Button size="lg" asChild>
              <Link href="/signup">Get Started</Link>
            </Button>
            <Button variant="outline" size="lg" asChild>
              <Link href="/about">Learn More</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="w-full px-4 py-24 bg-muted/50">
        <div className="w-full">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight">Built for Security Analysts</h2>
            <p className="mt-4 text-lg text-muted-foreground">
              Everything you need to analyze, automate, and respond to security threats
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <Shield className="h-10 w-10 text-red-600" />
                <CardTitle>Threat Detection</CardTitle>
                <CardDescription>
                  Advanced analytics for identifying and analyzing security threats in real-time
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <Workflow className="h-10 w-10 text-blue-600" />
                <CardTitle>Workflow Automation</CardTitle>
                <CardDescription>
                  Seamless integration with n8n and Airflow for automated security workflows
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <BarChart3 className="h-10 w-10 text-green-600" />
                <CardTitle>Analytics Dashboard</CardTitle>
                <CardDescription>Comprehensive dashboards with real-time metrics and security insights</CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <Key className="h-10 w-10 text-purple-600" />
                <CardTitle>API Management</CardTitle>
                <CardDescription>
                  Secure API key management for integrating with external security tools
                </CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <Zap className="h-10 w-10 text-yellow-600" />
                <CardTitle>Fast Response</CardTitle>
                <CardDescription>Lightning-fast incident response with automated playbooks and alerts</CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <Lock className="h-10 w-10 text-indigo-600" />
                <CardTitle>Enterprise Security</CardTitle>
                <CardDescription>
                  Bank-level security with encryption, audit logs, and compliance features
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="w-full px-4 py-24">
        <div className="w-full text-center">
          <h2 className="text-3xl font-bold tracking-tight">Ready to enhance your security operations?</h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Join thousands of security analysts who trust RedMap for their cybersecurity needs.
          </p>
          <div className="mt-8">
            <Button size="lg" asChild>
              <Link href="/signup">Start Free Trial</Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  )
}
