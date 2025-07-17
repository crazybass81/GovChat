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

export async function POST(request: NextRequest) {
  try {
    const { email } = await request.json();
    
    // 이메일 형식 검증
    if (!email || !email.includes('@')) {
      return NextResponse.json(
        { error: '유효한 이메일 주소를 입력하세요.' },
        { status: 400 }
      );
    }

    // 관리자 계정 확인
    const adminResult = await dynamoClient.get({
      TableName: 'AdminUsers',
      Key: { email }
    });

    // 계정이 존재하지 않아도 성공 응답 (보안상 이유)
    if (!adminResult.Item) {
      console.log(`아이디 찾기 요청: 계정 없음 - ${email}`);
      return NextResponse.json({
        success: true,
        message: '아이디 정보가 이메일로 발송되었습니다.'
      });
    }

    // 이메일 발송 (실제 환경에서는 SES 등을 사용)
    console.log(`아이디 찾기 이메일 발송 (개발 환경): ${email}`);
    console.log(`이메일 내용: 귀하의 GovChat 관리자 아이디는 ${email} 입니다.`);

    return NextResponse.json({
      success: true,
      message: '아이디 정보가 이메일로 발송되었습니다.'
    });
  } catch (error) {
    console.error('아이디 찾기 요청 오류:', error);
    return NextResponse.json(
      { error: '아이디 찾기 요청 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}