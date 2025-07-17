import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocument } from '@aws-sdk/lib-dynamodb';
import { randomUUID } from 'crypto';
import bcrypt from 'bcryptjs';

const dynamoClient = DynamoDBDocument.from(new DynamoDBClient({
  region: 'us-east-1',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
}));

// 관리자 목록 조회
export async function GET() {
  try {
    // 세션 확인 (마스터 관리자만 접근 가능)
    const session = await getServerSession();
    if (!session?.user?.email || session.user.role !== 'master') {
      return NextResponse.json(
        { error: '권한이 없습니다.' },
        { status: 403 }
      );
    }

    // UserTable에서 관리자 목록 조회
    const result = await dynamoClient.scan({
      TableName: 'UserTable',
      FilterExpression: 'user_type = :admin OR user_type = :master',
      ExpressionAttributeValues: {
        ':admin': 'admin',
        ':master': 'master'
      },
      ProjectionExpression: 'email, user_type, #name, created_at, active, email_verified',
      ExpressionAttributeNames: {
        '#name': 'name'
      }
    });

    const admins = result.Items || [];
    
    return NextResponse.json({ admins });
  } catch (error) {
    console.error('관리자 목록 조회 오류:', error);
    return NextResponse.json(
      { error: '관리자 목록을 불러오는 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}

// 새 관리자 초대
export async function POST(request: NextRequest) {
  try {
    // 세션 확인 (마스터 관리자만 접근 가능)
    const session = await getServerSession();
    if (!session?.user?.email || session.user.role !== 'master') {
      return NextResponse.json(
        { error: '권한이 없습니다.' },
        { status: 403 }
      );
    }

    const { email } = await request.json();
    
    // 이메일 형식 검증
    if (!email || !email.includes('@')) {
      return NextResponse.json(
        { error: '유효한 이메일 주소를 입력하세요.' },
        { status: 400 }
      );
    }

    // 이미 존재하는 사용자인지 확인
    const existingUser = await dynamoClient.get({
      TableName: 'UserTable',
      Key: { email }
    });

    if (existingUser.Item) {
      return NextResponse.json(
        { error: '이미 등록된 사용자입니다.' },
        { status: 400 }
      );
    }

    // 초대 토큰 생성
    const resetToken = randomUUID();
    const tokenExpiry = new Date();
    tokenExpiry.setHours(tokenExpiry.getHours() + 24); // 24시간 후 만료

    // 새 관리자 등록
    await dynamoClient.put({
      TableName: 'UserTable',
      Item: {
        email,
        user_type: 'admin', // 마스터가 아닌 일반 관리자로 등록
        password_hash: '<INVITE_PENDING>',
        reset_token: resetToken,
        token_expiry: tokenExpiry.toISOString(),
        active: false, // 비밀번호 설정 전까지 비활성
        email_verified: false,
        created_at: new Date().toISOString()
      }
    });

    // 이메일 발송 (실제 환경에서는 SES 등을 사용)
    console.log(`초대 이메일 발송 (개발 환경): ${email}`);
    console.log(`초대 링크: ${process.env.NEXTAUTH_URL}/admin/reset-password?token=${resetToken}`);

    return NextResponse.json({
      success: true,
      message: '관리자 초대가 발송되었습니다.',
      email
    });
  } catch (error) {
    console.error('관리자 초대 오류:', error);
    return NextResponse.json(
      { error: '관리자 초대 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}

// 관리자 삭제
export async function DELETE(request: NextRequest) {
  try {
    // 세션 확인 (마스터 관리자만 접근 가능)
    const session = await getServerSession();
    if (!session?.user?.email || session.user.role !== 'master') {
      return NextResponse.json(
        { error: '권한이 없습니다.' },
        { status: 403 }
      );
    }

    const { email } = await request.json();
    
    // 마스터 계정은 삭제 불가
    const userResult = await dynamoClient.get({
      TableName: 'UserTable',
      Key: { email }
    });

    if (!userResult.Item) {
      return NextResponse.json(
        { error: '존재하지 않는 사용자입니다.' },
        { status: 404 }
      );
    }

    if (userResult.Item.user_type === 'master') {
      return NextResponse.json(
        { error: '마스터 계정은 삭제할 수 없습니다.' },
        { status: 400 }
      );
    }

    // 관리자 삭제
    await dynamoClient.delete({
      TableName: 'UserTable',
      Key: { email }
    });

    return NextResponse.json({
      success: true,
      message: '관리자가 삭제되었습니다.',
      email
    });
  } catch (error) {
    console.error('관리자 삭제 오류:', error);
    return NextResponse.json(
      { error: '관리자 삭제 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}