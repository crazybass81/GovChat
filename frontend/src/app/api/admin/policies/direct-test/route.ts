import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { apiUrl, serviceKey, params = {} } = body
    
    const urlParams = new URLSearchParams({
      serviceKey: serviceKey,
      ...params
    })

    const response = await fetch(`${apiUrl}?${urlParams}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    })

    const responseText = await response.text()
    let responseData
    try {
      responseData = JSON.parse(responseText)
    } catch {
      responseData = { raw_response: responseText }
    }

    // 파이프라인 테스트
    let pipelineResult = null
    if (response.ok) {
      try {
        const testData = {
          id: `test_${Date.now()}`,
          title: '창업지원 테스트 프로그램',
          description: '테스트용 창업지원 프로그램입니다.',
          agency: '창업진흥원'
        }

        const pipelineResponse = await fetch('/api/admin/policies/test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ test_data: testData })
        })

        if (pipelineResponse.ok) {
          pipelineResult = await pipelineResponse.json()
        }
      } catch (pipelineError) {
        console.error('Pipeline test error:', pipelineError)
      }
    }

    return NextResponse.json({
      success: response.ok,
      api_test: {
        status: response.status,
        response_data: responseData
      },
      pipeline_test: pipelineResult
    })

  } catch (error) {
    return NextResponse.json(
      { 
        error: 'API 테스트 실패',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}