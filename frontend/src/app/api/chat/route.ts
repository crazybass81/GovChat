import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, sessionId } = body;

    // Mock 응답 데이터
    const mockResponse = {
      message: `안녕하세요! "${message}"에 대해 도움을 드리겠습니다.`,
      type: 'response',
      sessionId: sessionId || 'default',
      suggestions: [
        '청년 창업 지원사업',
        '중소기업 성장 지원금',
        '취업 지원 프로그램'
      ]
    };

    return NextResponse.json(mockResponse);
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function GET() {
  return NextResponse.json({
    status: 'Chat API is running',
    version: '1.0.0'
  });
}