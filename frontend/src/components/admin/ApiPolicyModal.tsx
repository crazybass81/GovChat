import React, { useState } from 'react';
import { Modal } from '@/components/ui/modal';

interface ApiPolicyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function ApiPolicyModal({ isOpen, onClose, onSuccess }: ApiPolicyModalProps) {
  const [urls, setUrls] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!urls.trim()) return;

    // 줄바꿈으로 URL 분리
    const urlList = urls.split('\n')
      .map(url => url.trim())
      .filter(url => url.length > 0);

    if (urlList.length === 0) return;

    setIsSubmitting(true);
    try {
      const response = await fetch('/api/admin/policies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'api', urls: urlList })
      });

      if (response.ok) {
        onSuccess();
        onClose();
        setUrls('');
      } else {
        const data = await response.json();
        alert(`등록 실패: ${data.error || '알 수 없는 오류'}`);
      }
    } catch (error) {
      alert('정책 등록 중 오류가 발생했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="정책등록 (API 정보)">
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">
            API 관련 URL 목록
          </label>
          <textarea
            value={urls}
            onChange={(e) => setUrls(e.target.value)}
            className="w-full p-2 border rounded h-40"
            placeholder="API 문서 URL을 한 줄에 하나씩 입력하세요.
예시:
https://www.data.go.kr/tcs/dss/selectApiDataDetailView.do?publicDataPk=15001107
https://api.odcloud.kr/api/gov24/v1/serviceInfo"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            API 문서, 개발자 가이드, 포털 페이지 등의 URL을 입력하세요. 시스템이 자동으로 정보를 추출합니다.
          </p>
        </div>

        <div className="flex justify-end space-x-2 mt-6">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm border rounded"
          >
            취소
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded disabled:opacity-50"
          >
            {isSubmitting ? '처리 중...' : '등록'}
          </button>
        </div>
      </form>
    </Modal>
  );
}