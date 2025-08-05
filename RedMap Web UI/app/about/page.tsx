import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Shield, Users, Globe, Award, Target, Zap, Lock, BarChart3 } from "lucide-react"

export default function AboutPage() {
  const team = [
    {
      name: "Alex Thompson",
      role: "Lead Security Researcher",
      background: "AI & Machine Learning Expert",
      expertise: "Threat Detection AI",
    },
    {
      name: "Sarah Martinez",
      role: "Senior Cybersecurity Analyst",
      background: "10+ years SOC experience",
      expertise: "Incident Response",
    },
    {
      name: "Dr. Michael Chen",
      role: "AI Research Director",
      background: "PhD in Computer Science",
      expertise: "Deep Learning Security",
    },
    {
      name: "Jessica Rodriguez",
      role: "Security Automation Engineer",
      background: "DevSecOps Specialist",
      expertise: "Workflow Automation",
    },
  ]

  const stats = [
    { label: "Security Analysts", value: "10,000+", icon: Users },
    { label: "Threats Detected", value: "2.5M+", icon: Shield },
    { label: "Countries Served", value: "45+", icon: Globe },
    { label: "Uptime", value: "99.9%", icon: Award },
  ]

  return (
    <div className="w-full px-4 py-8">
      {/* Hero Section */}
      <div className="text-center mb-16">
        <h1 className="text-4xl font-bold mb-4">About RedMap</h1>
        <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
          We're building the future of cybersecurity analytics, empowering security teams with intelligent automation
          and comprehensive threat detection capabilities.
        </p>
      </div>

      {/* Stats */}
      <div className="grid gap-6 md:grid-cols-4 mb-16">
        {stats.map((stat, index) => (
          <Card key={index} className="text-center">
            <CardContent className="pt-6">
              <stat.icon className="h-8 w-8 mx-auto mb-2 text-primary" />
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-sm text-muted-foreground">{stat.label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Mission & Vision */}
      <div className="grid gap-8 md:grid-cols-2 mb-16">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-6 w-6 text-red-600" />
              Our Mission
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              To empower cybersecurity analysts with the power of artificial intelligence. We believe that by combining
              human expertise with advanced AI capabilities, we can revolutionize how security teams detect, analyze,
              and respond to cyber threats. Our mission is to make every analyst more effective through intelligent
              automation and AI-driven insights.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-6 w-6 text-yellow-600" />
              Our Vision
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              A world where cyber threats are detected and neutralized before they can cause harm. We envision a future
              where AI-powered security platforms work seamlessly with human expertise to create an impenetrable defense
              against evolving cyber threats.
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Core Values */}
      <Card className="mb-16">
        <CardHeader>
          <CardTitle>Our Core Values</CardTitle>
          <CardDescription>The principles that guide everything we do</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-3">
            <div className="text-center">
              <Lock className="h-8 w-8 mx-auto mb-3 text-blue-600" />
              <h3 className="font-semibold mb-2">Security First</h3>
              <p className="text-sm text-muted-foreground">
                Security isn't just our product—it's embedded in our culture, processes, and every decision we make.
              </p>
            </div>

            <div className="text-center">
              <Users className="h-8 w-8 mx-auto mb-3 text-green-600" />
              <h3 className="font-semibold mb-2">Customer Obsession</h3>
              <p className="text-sm text-muted-foreground">
                We listen to our users and build solutions that solve real problems faced by security professionals.
              </p>
            </div>

            <div className="text-center">
              <BarChart3 className="h-8 w-8 mx-auto mb-3 text-purple-600" />
              <h3 className="font-semibold mb-2">Continuous Innovation</h3>
              <p className="text-sm text-muted-foreground">
                We constantly push boundaries, embracing new technologies to stay ahead of emerging threats.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Team */}
      <Card className="mb-16">
        <CardHeader>
          <CardTitle>Meet Our Team</CardTitle>
          <CardDescription>Security experts and technologists working to protect the digital world</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {team.map((member, index) => (
              <div key={index} className="text-center">
                <div className="w-24 h-24 bg-gradient-to-br from-red-100 to-red-200 dark:from-red-900 dark:to-red-800 rounded-full mx-auto mb-4 flex items-center justify-center">
                  <div className="w-16 h-16 bg-red-600 rounded-full flex items-center justify-center">
                    <span className="text-white font-bold text-lg">
                      {member.name
                        .split(" ")
                        .map((n) => n[0])
                        .join("")}
                    </span>
                  </div>
                </div>
                <h3 className="font-semibold">{member.name}</h3>
                <p className="text-sm text-primary mb-2">{member.role}</p>
                <p className="text-xs text-muted-foreground mb-2">{member.background}</p>
                <Badge variant="outline" className="text-xs">
                  {member.expertise}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Technology Stack */}
      <Card className="mb-16">
        <CardHeader>
          <CardTitle>Technology & Integrations</CardTitle>
          <CardDescription>
            Built on modern, scalable technologies with extensive integration capabilities
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-8 md:grid-cols-2">
            <div>
              <h3 className="font-semibold mb-4">Core Technologies</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Next.js & React</span>
                  <Badge variant="outline">Frontend</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Node.js & Python</span>
                  <Badge variant="outline">Backend</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">PostgreSQL & Redis</span>
                  <Badge variant="outline">Database</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Kubernetes & Docker</span>
                  <Badge variant="outline">Infrastructure</Badge>
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold mb-4">Key Integrations</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">n8n Workflows</span>
                  <Badge variant="outline">Automation</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Apache Airflow</span>
                  <Badge variant="outline">Data Pipeline</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">SIEM Platforms</span>
                  <Badge variant="outline">Security</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Threat Intelligence APIs</span>
                  <Badge variant="outline">Intelligence</Badge>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Contact */}
      <Card>
        <CardHeader>
          <CardTitle>Get in Touch</CardTitle>
          <CardDescription>Have questions or want to learn more about RedMap?</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="text-center">
              <h4 className="font-semibold mb-2">Sales</h4>
              <p className="text-sm text-muted-foreground">sales@redmap.com</p>
              <p className="text-sm text-muted-foreground">+1 (555) 123-4567</p>
            </div>

            <div className="text-center">
              <h4 className="font-semibold mb-2">Support</h4>
              <p className="text-sm text-muted-foreground">support@redmap.com</p>
              <p className="text-sm text-muted-foreground">24/7 Available</p>
            </div>

            <div className="text-center">
              <h4 className="font-semibold mb-2">Partnerships</h4>
              <p className="text-sm text-muted-foreground">partners@redmap.com</p>
              <p className="text-sm text-muted-foreground">Business Hours</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
