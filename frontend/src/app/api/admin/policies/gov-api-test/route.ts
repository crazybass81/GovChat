import { NextRequest, NextResponse } from 'next/server'

// 창업진흥원 K-Startup API 키
const KSTARTUP_API_KEY = '0259O7%2FMNmML1Vc3Q2zGYep%2FIdldHAOqicKRLBU4TllZmDrPwGdRMZas3F4ZIA0ccVHIv%2Fdxa%2BUvOzEtsxCRzA%3D%3D'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { pageNo = 1, numOfRows = 10 } = body
    
    // 창업진흥원 K-Startup API 호출
    const govApiUrl = `https://apis.data.go.kr/B552735/kisedKstartupService01/getBizAnnouncementList`
    const params = new URLSearchParams({
      serviceKey: KSTARTUP_API_KEY,
      numOfRows: numOfRows.toString(),
      pageNo: pageNo.toString(),
      resultType: 'json'
    })

    const response = await fetch(`${govApiUrl}?${params}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error(`Government API error: ${response.status} ${response.statusText}`)
    }

    const govData = await response.json()
    
    // 데이터 처리 파이프라인 호출
    const processedPolicies = []
    
    const policyList = govData.response?.body?.items || []
    
    if (Array.isArray(policyList)) {
      for (const item of policyList.slice(0, 3)) {
        try {
          // 파이프라인 호출
          const pipelineResponse = await fetch('/api/admin/policies/process', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              source_type: 'api',
              raw_data: {
                id: item.announcementId || `kstartup_${Date.now()}`,
                title: item.announcementTitle || 'Unknown Startup Program',
                description: item.announcementContent || item.businessContent || '',
                agency: '창업진흥원',
                target: item.targetGroup || item.applicationTarget || '',
                support_content: item.supportDetails || item.businessOverview || '',
                application_period: item.applicationPeriod || item.announcementPeriod || '',
                contact: item.contactInfo || item.inquiryContact || ''
              }
            })
          })

          if (pipelineResponse.ok) {
            const result = await pipelineResponse.json()
            processedPolicies.push({
              original: item,
              pipeline_result: result
            })
          }
        } catch (pipelineError) {
          console.error('Pipeline error:', pipelineError)
        }
      }
    }

    return NextResponse.json({
      success: true,
      message: `Processed ${processedPolicies.length} policies`,
      government_api_response: {
        total_count: govData.totalCount || 0,
        current_page: pageNo,
        items_per_page: numOfRows
      },
      processed_policies: processedPolicies,
      pipeline_summary: {
        total_processed: processedPolicies.length,
        successful_pipelines: processedPolicies.filter(p => p.pipeline_result?.success).length
      }
    })

  } catch (error) {
    console.error('Government API test error:', error)
    return NextResponse.json(
      { 
        error: 'Failed to test government API',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}