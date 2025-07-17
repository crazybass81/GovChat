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

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const policyId = params.id;
    
    // PoliciesTable에서 정책 상세 정보 조회
    const result = await dynamoClient.get({
      TableName: 'PoliciesTable',
      Key: { policy_id: policyId }
    });
    
    if (!result.Item) {
      return NextResponse.json(
        { error: '정책을 찾을 수 없습니다.' },
        { status: 404 }
      );
    }
    
    return NextResponse.json(result.Item);
  } catch (error) {
    console.error('정책 상세 조회 오류:', error);
    return NextResponse.json(
      { error: '정책 상세 정보를 불러오는 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const policyId = params.id;
    const data = await request.json();
    
    // 기존 정책 확인
    const existingPolicy = await dynamoClient.get({
      TableName: 'PoliciesTable',
      Key: { policy_id: policyId }
    });
    
    if (!existingPolicy.Item) {
      return NextResponse.json(
        { error: '수정할 정책을 찾을 수 없습니다.' },
        { status: 404 }
      );
    }
    
    // 업데이트할 필드 준비
    const updateData = {
      ...existingPolicy.Item,
      title: data.title || existingPolicy.Item.title,
      description: data.description || existingPolicy.Item.description,
      agency: data.agency || existingPolicy.Item.agency,
      target_audience: data.target_audience || existingPolicy.Item.target_audience,
      support_type: data.support_type || existingPolicy.Item.support_type,
      updated_at: new Date().toISOString()
    };
    
    // DynamoDB에 업데이트
    await dynamoClient.put({
      TableName: 'PoliciesTable',
      Item: updateData
    });
    
    return NextResponse.json({
      success: true,
      message: '정책이 업데이트되었습니다.',
      policy: updateData
    });
  } catch (error) {
    console.error('정책 업데이트 오류:', error);
    return NextResponse.json(
      { success: false, error: '정책 업데이트 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const policyId = params.id;
    
    // 정책 삭제
    await dynamoClient.delete({
      TableName: 'PoliciesTable',
      Key: { policy_id: policyId }
    });
    
    return NextResponse.json({
      success: true,
      message: '정책이 삭제되었습니다.'
    });
  } catch (error) {
    console.error('정책 삭제 오류:', error);
    return NextResponse.json(
      { success: false, error: '정책 삭제 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}