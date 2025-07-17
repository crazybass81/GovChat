import { NextRequest, NextResponse } from 'next/server';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocument } from '@aws-sdk/lib-dynamodb';

const dynamoClient = DynamoDBDocument.from(new DynamoDBClient({
  region: 'us-east-1',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
}));

export async function GET() {
  try {
    // PoliciesTable에서 정책 목록 조회
    const result = await dynamoClient.scan({
      TableName: 'PoliciesTable',
      Limit: 100 // 최대 100개까지 조회
    });
    
    const policies = result.Items || [];
    
    // 프론트엔드에 필요한 형식으로 변환
    const formattedPolicies = policies.map(policy => ({
      policy_id: policy.policy_id,
      title: policy.title || '제목 없음',
      agency: policy.agency || '기관 미상',
      last_updated: policy.updated_at || policy.created_at || new Date().toISOString(),
      active: policy.active === undefined ? true : policy.active
    }));
    
    return NextResponse.json({ policies: formattedPolicies });
  } catch (error) {
    console.error('정책 목록 조회 오류:', error);
    return NextResponse.json(
      { error: '정책 목록을 불러오는 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    // JSON 처리 - FormData 처리는 일단 제외
    // 파일 업로드는 추후 구현
    
      const data = await request.json();
      const { type, url, urls, title, description, agency } = data;
      
      // 정책 ID 생성
      const policyId = `policy_${Date.now()}`;
      
      // 기본 정책 데이터
      const policyData: any = {
        policy_id: policyId,
        title: title || '새 정책',
        description: description || '',
        agency: agency || '',
        source: type || 'manual',
        created_at: new Date().toISOString(),
        active: true
      };
      
      // URL 입력 방식
      if (type === 'url' && url) {
        policyData.original_url = url;
        policyData.title = `URL 정책: ${new URL(url).hostname}`;
      }
      
      // API 정보 방식
      if (type === 'api' && urls && Array.isArray(urls)) {
        policyData.api_urls = urls;
        policyData.title = `API 정책: ${urls.length}개 문서`;
      }
      
      // DynamoDB에 저장
      await dynamoClient.put({
        TableName: 'PoliciesTable',
        Item: policyData
      });
      
      // 파이프라인 호출
      try {
        await fetch('/api/admin/run-pipeline', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ apiId: policyId })
        });
      } catch (pipelineError) {
        console.error('파이프라인 호출 오류:', pipelineError);
        // 파이프라인 오류는 무시하고 정책 등록은 성공으로 처리
      }
      
      return NextResponse.json({
        success: true,
        message: '정책이 등록되었습니다.',
        policy: policyData
      });
    }
  } catch (error) {
    console.error('정책 등록 오류:', error);
    return NextResponse.json(
      { success: false, error: '정책 등록 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}