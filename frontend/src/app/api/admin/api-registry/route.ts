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
    const { apiInfo } = await request.json();

    // 직접 AI 파싱 및 테스트
    const result = await autoRegisterAPI(apiInfo);
    return NextResponse.json(result);

  } catch (error) {
    console.error('API Registry Error:', error);
    return NextResponse.json(
      { success: false, error: '서버 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}

async function autoRegisterAPI(apiInfo: string) {
  // AI 파싱
  const parsed = parseAPIInfo(apiInfo);
  
  if (!parsed.url) {
    return {
      success: false,
      error: "API URL을 찾을 수 없습니다."
    };
  }
  
  // 기본 검증
  const isValid = parsed.url && parsed.url.startsWith('http') && parsed.serviceKey;
  
  if (isValid) {
    // API 등록 및 테스트
    const apiId = `api_${Date.now()}`;
    const apiConfig = {
      id: apiId,
      name: parsed.name || "Auto Registered API",
      url: parsed.url,
      serviceKey: parsed.serviceKey,
      createdAt: new Date().toISOString()
    };
    
    // API 연결 테스트
    const testResult = await testAPI(apiConfig);
    
    if (testResult.success) {
      // 테스트 성공 시 DB에 저장
      await saveAPIConfig(apiConfig);
      
      return {
        success: true,
        message: "✅ API 등록 및 테스트 완료",
        api: {
          id: apiId,
          name: parsed.name || "Auto Registered API",
          url: parsed.url
        },
        testResult: {
          recordCount: testResult.recordCount || 0,
          responseSize: testResult.responseSize || 0,
          status: "데이터 파이프라인 실행 준비 완료"
        }
      };
    } else {
      // 테스트 실패 시
      return {
        success: false,
        error: `API 테스트 실패: ${testResult.error}`,
        api: {
          name: parsed.name || "Auto Registered API",
          url: parsed.url
        }
      };
    }
  } else {
    const missing = [];
    if (!parsed.url) missing.push("URL");
    if (!parsed.serviceKey) missing.push("API 키");
    
    return {
      success: false,
      error: `❌ 필수 정보 누락: ${missing.join(", ")}`
    };
  }
}

async function testAPIConnection(config: any) {
  try {
    const url = new URL(config.url);
    if (config.serviceKey) {
      url.searchParams.set('serviceKey', decodeURIComponent(config.serviceKey));
    }
    url.searchParams.set('numOfRows', '1');
    url.searchParams.set('pageNo', '1');
    
    const response = await fetch(url.toString());
    
    if (response.ok) {
      return { success: true };
    } else {
      return { success: false, error: `HTTP ${response.status}` };
    }
  } catch (error) {
    return { success: false, error: error instanceof Error ? error.message : 'Connection failed' };
  }
}

async function saveAPIConfig(apiConfig: any) {
  try {
    // API 설정을 DynamoDB에 저장
    await dynamoClient.put({
      TableName: 'APIConfigTable',
      Item: {
        api_id: apiConfig.id,
        name: apiConfig.name,
        url: apiConfig.url,
        serviceKey: apiConfig.serviceKey, // 실제 환경에서는 암호화 필요
        createdAt: apiConfig.createdAt,
        status: 'active'
      }
    });
    
    console.log('API config registered in DynamoDB:', apiConfig.id);
    return true;
  } catch (error) {
    console.error('Failed to save API config:', error);
    throw error;
  }
}

// 데이터 처리 파이프라인 실행 함수 (별도 엔드포인트에서 호출)
export async function runDataPipeline(apiId: string) {
  // 1. API에서 데이터 추출
  // 2. 웹사이트 크롤링
  // 3. AI 분석 및 조건 추출
  // 4. 데이터베이스 저장
  // 5. 임베딩 및 오픈서치 인덱싱
  console.log('Data pipeline would run for API:', apiId);
}

function parseAPIInfo(apiInfo: string) {
  const result: any = {};
  
  // URL 추출
  const urlMatch = apiInfo.match(/https?:\/\/[^\s]+/);
  if (urlMatch) {
    result.url = urlMatch[0];
  }
  
  // 서비스명 추출
  const nameMatch = apiInfo.match(/서비스명[:\s]*([^\n]+)/);
  if (nameMatch) {
    result.name = nameMatch[1].trim();
  } else {
    result.name = "Auto Registered API";
  }
  
  // 인증키 추출 (더 유연하게)
  const keyPatterns = [
    /인증키[:\s]*([^\s\n]+)/,
    /serviceKey[=:\s]*([^\s&\n]+)/i,
    /API[_\s]*KEY[:\s]*([^\s\n]+)/i
  ];
  
  for (const pattern of keyPatterns) {
    const match = apiInfo.match(pattern);
    if (match) {
      result.serviceKey = decodeURIComponent(match[1].trim());
      break;
    }
  }
  
  console.log('Parsed API info:', result);
  return result;
}

async function testAPI(config: any) {
  try {
    if (!config.url) {
      return { success: false, error: 'URL not found' };
    }
    
    const url = new URL(config.url);
    if (config.serviceKey) {
      // URL 인코딩 제거 후 다시 인코딩
      const cleanKey = decodeURIComponent(config.serviceKey);
      url.searchParams.set('serviceKey', cleanKey);
    }
    url.searchParams.set('numOfRows', '5');
    url.searchParams.set('pageNo', '1');
    
    console.log('Testing URL:', url.toString());
    
    const response = await fetch(url.toString(), { 
      method: 'GET'
    });
    
    const text = await response.text();
    console.log('API Response:', response.status, text.substring(0, 500));
    
    if (response.ok) {
      const recordCount = (text.match(/<item>/g) || []).length;
      
      return {
        success: true,
        recordCount,
        responseSize: text.length
      };
    } else {
      // API 키 오류 메시지 확인
      if (text.includes('인증키') || text.includes('SERVICE_KEY') || text.includes('INVALID')) {
        return {
          success: false,
          error: 'API 키가 잘못되었거나 만료되었습니다. 새로운 API 키를 발급받아주세요.'
        };
      }
      
      return {
        success: false,
        error: `서버 오류 (${response.status}): API 키를 확인해주세요.`
      };
    }
  } catch (error) {
    console.error('API test error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}