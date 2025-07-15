import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { source_type, raw_data } = body
    
    if (!source_type || !raw_data) {
      return NextResponse.json(
        { error: 'source_type and raw_data are required' },
        { status: 400 }
      )
    }

    // Lambda 함수 호출
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE}/policy/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        source_type,
        raw_data
      })
    })

    if (!response.ok) {
      throw new Error(`Processing failed: ${response.statusText}`)
    }

    const result = await response.json()
    
    return NextResponse.json({
      success: true,
      execution_arn: result.execution_arn,
      s3_key: result.s3_key,
      message: 'Policy processing started'
    })

  } catch (error) {
    console.error('Policy processing error:', error)
    return NextResponse.json(
      { error: 'Processing failed' },
      { status: 500 }
    )
  }
}