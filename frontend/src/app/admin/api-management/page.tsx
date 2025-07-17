'use client';

import { useState, useEffect } from 'react';

export default function ApiManagementPage() {
  const [apiInfo, setApiInfo] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [opensearchStatus, setOpensearchStatus] = useState<any>(null);
  const [checkingStatus, setCheckingStatus] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsProcessing(true);
    setResult(null);

    try {
      const response = await fetch('/api/admin/api-registry', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ apiInfo })
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ success: false, error: '처리 중 오류가 발생했습니다.' });
    } finally {
      setIsProcessing(false);
    }
  };

  // OpenSearch 상태 확인
  const checkOpenSearchStatus = async () => {
    setCheckingStatus(true);
    try {
      const response = await fetch('/api/admin/opensearch-status');
      const data = await response.json();
      setOpensearchStatus(data);
    } catch (error) {
      setOpensearchStatus({
        status: 'error',
        message: '상태 확인 중 오류가 발생했습니다.'
      });
    } finally {
      setCheckingStatus(false);
    }
  };

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">API 자동 등록</h1>
        <button
          onClick={checkOpenSearchStatus}
          disabled={checkingStatus}
          className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50"
        >
          {checkingStatus ? 'OpenSearch 상태 확인 중...' : 'OpenSearch 상태 확인'}
        </button>
      </div>

      {opensearchStatus && (
        <div className={`mb-6 p-4 rounded-lg ${opensearchStatus.status === 'ok' ? 'bg-green-50' : 'bg-red-50'}`}>
          <h3 className="font-bold mb-2">
            {opensearchStatus.status === 'ok' ? '✅ OpenSearch 정상' : '❌ OpenSearch 오류'}
          </h3>
          <p>{opensearchStatus.message}</p>
          {opensearchStatus.details && (
            <div className="mt-2 text-sm">
              <p><strong>클러스터 상태:</strong> {opensearchStatus.details.clusterStatus}</p>
              <p><strong>인덱스 존재:</strong> {opensearchStatus.details.indexExists ? '예' : '아니오'}</p>
              <p><strong>노드 수:</strong> {opensearchStatus.details.numberOfNodes}</p>
              <p><strong>활성 샤드:</strong> {opensearchStatus.details.activePrimaryShards}</p>
            </div>
          )}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">
            API 키 정보 (전체 복사해서 붙여넣기)
          </label>
          <textarea
            value={apiInfo}
            onChange={(e) => setApiInfo(e.target.value)}
            className="w-full h-64 p-3 border rounded-lg"
            placeholder="예시:
서비스명: K-Startup 창업지원 정보
API URL: https://nidapi.k-startup.go.kr/api/kisedKstartupService/v1/getBusinessInformation
인증키: 0259O7/MNmML1Vc3Q2zGYep/...
파라미터: numOfRows=50&pageNo=1
응답형식: XML

또는 공공데이터포털에서 복사한 API 정보를 그대로 붙여넣으세요."
            required
          />
        </div>

        <button
          type="submit"
          disabled={isProcessing}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {isProcessing ? 'AI 분석 및 테스트 중...' : 'API 자동 등록'}
        </button>
      </form>

      {result && (
        <div className={`mt-6 p-4 rounded-lg ${result.success ? 'bg-green-50' : 'bg-red-50'}`}>
          <h3 className="font-bold mb-2">
            {result.success ? '✅ 등록 성공' : '❌ 등록 실패'}
          </h3>
          
          {result.success && (
            <div className="space-y-2">
              <p><strong>API 이름:</strong> {result.api.name}</p>
              <p><strong>엔드포인트:</strong> {result.api.url}</p>
              <p><strong>테스트 결과:</strong> {result.testResult.recordCount}개 데이터 수집 성공</p>
            </div>
          )}
          
          {result.error && (
            <p className="text-red-600">{result.error}</p>
          )}
        </div>
      )}
    </div>
  );
}