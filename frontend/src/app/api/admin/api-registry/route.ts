import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { apiInfo } = await request.json();

    // Lambda 함수 호출
    const response = await fetch(process.env.LAMBDA_API_URL + '/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        action: 'auto_register',
        apiInfo
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const result = await response.json();
    return NextResponse.json({ success: true, result });

  } catch (error) {
    console.error('API Registry Error:', error);
    return NextResponse.json(
      { success: false, error: '서버 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}