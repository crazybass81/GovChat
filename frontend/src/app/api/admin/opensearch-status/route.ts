import { NextResponse } from 'next/server';
import { checkOpenSearchStatus } from '@/lib/opensearch';

export async function GET() {
  try {
    const status = await checkOpenSearchStatus();
    return NextResponse.json(status);
  } catch (error) {
    console.error('OpenSearch 상태 확인 오류:', error);
    return NextResponse.json(
      { 
        status: 'error',
        message: 'OpenSearch 상태 확인 중 오류가 발생했습니다.',
        error: error instanceof Error ? error.message : String(error)
      },
      { status: 500 }
    );
  }
}