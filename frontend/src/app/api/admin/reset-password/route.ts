import { NextRequest, NextResponse } from 'next/server';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocument } from '@aws-sdk/lib-dynamodb';
import bcrypt from 'bcryptjs';

const dynamoClient = DynamoDBDocument.from(new DynamoDBClient({
  region: 'us-east-1',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
}));

// 토큰 유효성 검증
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const token = searchParams.get('token');

    if (!token) {
      return NextResponse.json(
        { error: '토큰이 제공되지 않았습니다.' },
        { status: 400 }
      );
    }

    // 토큰으로 관리자 찾기
    const result = await dynamoClient.scan({
      TableName: 'AdminUsers',
      FilterExpression: 'reset_token = :token',
      ExpressionAttributeValues: {
        ':token': token
      }
    });

    if (!result.Items || result.Items.length === 0) {
      return NextResponse.json(
        { error: '유효하지 않은 토큰입니다.' },
        { status: 400 }
      );
    }

    const admin = result.Items[0];
    
    // 토큰 만료 확인
    if (admin.token_expiry && new Date(admin.token_expiry) < new Date()) {
      return NextResponse.json(
        { error: '만료된 토큰입니다. 비밀번호 재설정을 다시 요청하세요.' },
        { status: 400 }
      );
    }

    return NextResponse.json({
      valid: true,
      email: admin.email
    });
  } catch (error) {
    console.error('토큰 검증 오류:', error);
    return NextResponse.json(
      { error: '토큰 검증 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}

// 비밀번호 재설정
export async function POST(request: NextRequest) {
  try {
    const { token, password } = await request.json();

    if (!token || !password) {
      return NextResponse.json(
        { error: '토큰과 비밀번호가 필요합니다.' },
        { status: 400 }
      );
    }

    // 비밀번호 유효성 검증
    if (password.length < 8) {
      return NextResponse.json(
        { error: '비밀번호는 최소 8자 이상이어야 합니다.' },
        { status: 400 }
      );
    }

    // 토큰으로 관리자 찾기
    const result = await dynamoClient.scan({
      TableName: 'AdminUsers',
      FilterExpression: 'reset_token = :token',
      ExpressionAttributeValues: {
        ':token': token
      }
    });

    if (!result.Items || result.Items.length === 0) {
      return NextResponse.json(
        { error: '유효하지 않은 토큰입니다.' },
        { status: 400 }
      );
    }

    const admin = result.Items[0];
    
    // 토큰 만료 확인
    if (admin.token_expiry && new Date(admin.token_expiry) < new Date()) {
      return NextResponse.json(
        { error: '만료된 토큰입니다. 비밀번호 재설정을 다시 요청하세요.' },
        { status: 400 }
      );
    }

    // 비밀번호 해싱
    const hashedPassword = await bcrypt.hash(password, 10);

    // 비밀번호 업데이트 및 토큰 제거
    await dynamoClient.update({
      TableName: 'AdminUsers',
      Key: { email: admin.email },
      UpdateExpression: 'SET password_hash = :password, invited = :invited REMOVE reset_token, token_expiry',
      ExpressionAttributeValues: {
        ':password': hashedPassword,
        ':invited': false
      }
    });

    return NextResponse.json({
      success: true,
      message: '비밀번호가 성공적으로 재설정되었습니다.'
    });
  } catch (error) {
    console.error('비밀번호 재설정 오류:', error);
    return NextResponse.json(
      { error: '비밀번호 재설정 중 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}