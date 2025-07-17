import { NextRequest, NextResponse } from 'next/server';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocument } from '@aws-sdk/lib-dynamodb';
import { LambdaClient, InvokeCommand } from '@aws-sdk/client-lambda';

const dynamoClient = DynamoDBDocument.from(new DynamoDBClient({
  region: 'us-east-1',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
}));

const lambdaClient = new LambdaClient({
  region: 'us-east-1',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const discoveryId = params.id;
    const { action } = await request.json();
    
    if (!['approve', 'reject'].includes(action)) {
      return NextResponse.json(
        { error: '유효하지 않은 액션입니다. "approve" 또는 "reject"만 가능합니다.' },
        { status: 400 }
      );
    }
    
    // 발굴된 정책 정보 조회
    const discoveryResult = await dynamoClient.get({
      TableName: 'PolicyDiscovery',
      Key: { id: discoveryId }
    });
    
    if (!discoveryResult.Item) {
      return NextResponse.json(
        { error: '발굴된 정책을 찾을 수 없습니다.' },
        { status: 404 }
      );
    }
    
    const discoveryItem = discoveryResult.Item;
    
    // 상태 업데이트
    await dynamoClient.update({
      TableName: 'PolicyDiscovery',
      Key: { id: discoveryId },
      UpdateExpression: 'SET #status = :status',
      ExpressionAttributeNames: {
        '#status': 'status'
      },
      ExpressionAttributeValues: {
        ':status': action === 'approve' ? 'approved' : 'rejected'
      }
    });
    
    // 승인인 경우 정책으로 등록
    if (action === 'approve') {
      try {
        // 정책 등록 처리
        const policyId = `disc_${Date.now()}`;
        
        // PoliciesTable에 저장
        await dynamoClient.put({
          TableName: 'PoliciesTable',
          Item: {
            policy_id: policyId,
            title: discoveryItem.title || '발굴된 정책',
            description: discoveryItem.description || '',
            agency: discoveryItem.source || '',
            source: 'discovery',
            original_url: discoveryItem.url || '',
            created_at: new Date().toISOString(),
            active: true,
            discovery_id: discoveryId
          }
        });
        
        // 발굴된 정책에 연결된 정책 ID 저장
        await dynamoClient.update({
          TableName: 'PolicyDiscovery',
          Key: { id: discoveryId },
          UpdateExpression: 'SET policy_id = :policyId',
          ExpressionAttributeValues: {
            ':policyId': policyId
          }
        });
        
        // 파이프라인 실행 (URL 기반)
        if (discoveryItem.url) {
          try {
            const functionName = 'GovChatStack-PolicyLambda1FF8B56B-9C1QXYMWFuBN';
            
            const params = {
              FunctionName: functionName,
              InvocationType: 'Event', // 비동기 호출
              Payload: JSON.stringify({
                action: 'process_url',
                url: discoveryItem.url,
                policyId: policyId
              })
            };
            
            const command = new InvokeCommand(params);
            await lambdaClient.send(command);
          } catch (lambdaError) {
            console.error('Lambda 호출 오류:', lambdaError);
            // 파이프라인 실패해도 정책은 등록됨
          }
        }
      } catch (policyError) {
        console.error('정책 등록 오류:', policyError);
        // 정책 등록 실패해도 상태는 approved로 변경됨
      }
    }
    
    return NextResponse.json({
      success: true,
      message: action === 'approve' ? '정책이 승인되었습니다.' : '정책이 거부되었습니다.',
      status: action === 'approve' ? 'approved' : 'rejected'
    });
  } catch (error) {
    console.error('정책 발굴 처리 오류:', error);
    return NextResponse.json(
      { success: false, error: '정책 발굴 처리 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}