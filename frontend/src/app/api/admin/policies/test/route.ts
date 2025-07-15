import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // 테스트용 샘플 데이터 처리
    const testResult = {
      policy_id: `test_${Date.now()}`,
      status: 'processed',
      pipeline_steps: {
        s3_storage: 'completed',
        parsing: 'completed', 
        condition_extraction: 'completed',
        embedding_generation: 'completed',
        clustering: 'completed',
        opensearch_indexing: 'completed'
      },
      extracted_conditions: {
        age_range: { min: 20, max: 39 },
        regions: ['서울', '경기'],
        target_groups: ['청년', '창업자'],
        support_type: '창업지원'
      },
      cluster_info: {
        cluster_id: 'startup_support_001',
        similarity_score: 0.87
      },
      processing_time: '2.3s'
    }
    
    return NextResponse.json({
      success: true,
      message: 'Test processing completed',
      data: testResult
    })

  } catch (error) {
    return NextResponse.json(
      { error: 'Test failed' },
      { status: 500 }
    )
  }
}