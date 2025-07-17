import React, { useState } from 'react';
import { Modal } from '@/components/ui/modal';

interface UrlPolicyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function UrlPolicyModal({ isOpen, onClose, onSuccess }: UrlPolicyModalProps) {
  const [url, setUrl] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setIsSubmitting(true);
    try {
      const response = await fetch('/api/admin/policies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'url', url })
      });

      if (response.ok) {
        onSuccess();
        onClose();
        setUrl('');
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
    <Modal isOpen={isOpen} onClose={onClose} title="정책등록 (URL 입력)">
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">
            정책 페이지 URL
          </label>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="w-full p-2 border rounded"
            placeholder="https://example.gov.kr/policy/123"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            정책 공고 페이지의 URL을 입력하세요. 시스템이 자동으로 내용을 분석합니다.
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