import { NextResponse } from 'next/server';
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
    // 테이블이 존재하는지 확인
    try {
      // PolicyDiscovery 테이블에서 발굴된 정책 목록 조회
      const result = await dynamoClient.scan({
        TableName: 'PolicyDiscovery',
        Limit: 50 // 최대 50개까지 조회
      });
      
      const discoveries = result.Items || [];
      
      return NextResponse.json({ discoveries });
    } catch (tableError) {
      console.warn('PolicyDiscovery 테이블이 없거나 접근할 수 없습니다:', tableError);
      
      // 테이블이 없는 경우 빈 배열 반환
      return NextResponse.json({ discoveries: [] });
    }
  } catch (error) {
    console.error('정책 발굴 목록 조회 오류:', error);
    return NextResponse.json(
      { error: '정책 발굴 목록을 불러오는 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}