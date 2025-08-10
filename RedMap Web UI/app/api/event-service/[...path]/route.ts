import { NextRequest, NextResponse } from 'next/server'
import axios from 'axios'

const getAuthHeader = () => {
    const apiKey = process.env.EVENT_SERVICE_API_KEY
    if (!apiKey) {
        throw new Error('Event Service API key is not set in .env')
    }
    return {
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': apiKey,
        },
    }
}

export async function GET(req: NextRequest) {
    const { pathname } = req.nextUrl
    const path = pathname.replace('/api/event-service/', '') || 'sources/status'
    const query = req.nextUrl.searchParams.toString()
    const url = `http://localhost:8002/api/event-service/${path}${query ? '?' + query : ''}`
    console.log('Proxying GET request to:', url)
    try {
        const response = await axios.get(url, getAuthHeader())
        return NextResponse.json(response.data)
    } catch (error: any) {
        console.error('Event Service API request failed:', error.message)
        return NextResponse.json(
            { error: error.message },
            { status: error.response?.status || 500 }
        )
    }
}

export async function POST(req: NextRequest) {
    const { pathname } = req.nextUrl
    const path = pathname.replace('/api/event-service/', '') || 'trigger'
    const query = req.nextUrl.searchParams.toString()
    const url = `http://localhost:8002/api/event-service/${path}${query ? '?' + query : ''}`
    const body = await req.json()
    console.log('Proxying POST request to:', url, 'with body:', body)
    try {
        const response = await axios.post(url, body, getAuthHeader())
        return NextResponse.json(response.data)
    } catch (error: any) {
        console.error('Event Service API request failed:', error.message)
        return NextResponse.json(
            { error: error.message },
            { status: error.response?.status || 500 }
        )
    }
}