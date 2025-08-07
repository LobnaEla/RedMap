import { NextRequest, NextResponse } from 'next/server'
import axios from 'axios'

const getAuthHeader = () => {
    const apiKey = process.env.N8N_API_KEY
    if (!apiKey) {
        console.error('n8n API key is not set in .env')
        throw new Error('n8n API key is not set')
    }
    return {
        headers: {
            'Content-Type': 'application/json',
            'X-N8N-API-KEY': apiKey,
        },
    }
}

export async function GET(req: NextRequest) {
    const { pathname } = req.nextUrl
    const path = pathname.replace('/api/n8n/', '') || 'workflows'
    const url = `http://localhost:5678/api/v1/${path}`
    try {
        const response = await axios.get(url, getAuthHeader())
        return NextResponse.json(response.data)
    } catch (error: any) {
        console.error('API request failed:', error.message, 'Response:', error.response?.data)
        return NextResponse.json({ error: error.message }, { status: error.response?.status || 500 })
    }
}

export async function POST(req: NextRequest) {
    const { pathname } = req.nextUrl
    const path = pathname.replace('/api/n8n/', '') || 'workflows'
    const url = `http://localhost:5678/api/v1/${path}`
    const body = await req.json()
    try {
        const response = await axios.post(url, body, getAuthHeader())
        return NextResponse.json(response.data)
    } catch (error: any) {
        console.error('API request failed:', error.message)
        return NextResponse.json({ error: error.message }, { status: error.response?.status || 500 })
    }
}