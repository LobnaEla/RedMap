import { NextRequest, NextResponse } from 'next/server'
import axios from 'axios'

const getAuthHeader = () => {
    const username = process.env.AIRFLOW_API_USERNAME
    const password = process.env.AIRFLOW_API_PASSWORD
    if (!username || !password) {
        throw new Error('Airflow API credentials are not set in .env')
    }
    return {
        headers: {
            'Content-Type': 'application/json',
            Authorization: `Basic ${Buffer.from(`${username}:${password}`).toString('base64')}`,
        },
    }
}

export async function GET(req: NextRequest) {
    const { pathname } = req.nextUrl
    const path = pathname.replace('/api/airflow/', '') || 'dags'
    const query = req.nextUrl.searchParams.toString()
    const url = `http://localhost:8080/api/v1/${path}${query ? '?' + query : ''}`
    console.log('Proxying GET request to:', url)
    try {
        const response = await axios.get(url, getAuthHeader())
        return NextResponse.json(response.data)
    } catch (error: any) {
        console.error('API request failed:', error.message)
        return NextResponse.json({ error: error.message }, { status: error.response?.status || 500 })
    }
}

export async function POST(req: NextRequest) {
    const { pathname } = req.nextUrl
    const path = pathname.replace('/api/airflow/', '') || 'dags'
    const query = req.nextUrl.searchParams.toString()
    const url = `http://localhost:8080/api/v1/${path}${query ? '?' + query : ''}`
    const body = await req.json()
    console.log('Proxying POST request to:', url, 'with body:', body)
    try {
        const response = await axios.post(url, body, getAuthHeader())
        return NextResponse.json(response.data)
    } catch (error: any) {
        console.error('API request failed:', error.message)
        return NextResponse.json({ error: error.message }, { status: error.response?.status || 500 })
    }
}