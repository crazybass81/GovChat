import { NextRequest, NextResponse } from 'next/server';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocument } from '@aws-sdk/lib-dynamodb';
import { randomUUID } from 'crypto';

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

    // 사용자 계정 확인
    const userResult = await dynamoClient.get({
      TableName: 'UserTable',
      Key: { email }
    });

    // 계정이 존재하지 않아도 성공 응답 (보안상 이유)
    if (!userResult.Item) {
      console.log(`비밀번호 재설정 요청: 계정 없음 - ${email}`);
      return NextResponse.json({
        success: true,
        message: '비밀번호 재설정 링크가 이메일로 발송되었습니다.'
      });
    }

    // 재설정 토큰 생성
    const resetToken = randomUUID();
    const tokenExpiry = new Date();
    tokenExpiry.setHours(tokenExpiry.getHours() + 1); // 1시간 후 만료

    // 토큰 저장
    await dynamoClient.update({
      TableName: 'UserTable',
      Key: { email },
      UpdateExpression: 'SET reset_token = :token, token_expiry = :expiry',
      ExpressionAttributeValues: {
        ':token': resetToken,
        ':expiry': tokenExpiry.toISOString()
      }
    });

    // 이메일 발송 (실제 환경에서는 SES 등을 사용)
    console.log(`비밀번호 재설정 이메일 발송 (개발 환경): ${email}`);
    console.log(`재설정 링크: ${process.env.NEXTAUTH_URL}/admin/reset-password?token=${resetToken}`);

    return NextResponse.json({
      success: true,
      message: '비밀번호 재설정 링크가 이메일로 발송되었습니다.'
    });
  } catch (error) {
    console.error('비밀번호 재설정 요청 오류:', error);
    return NextResponse.json(
      { error: '비밀번호 재설정 요청 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}