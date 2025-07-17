import React, { useState } from 'react';
import { Modal } from '@/components/ui/modal';

interface DocumentPolicyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function DocumentPolicyModal({ isOpen, onClose, onSuccess }: DocumentPolicyModalProps) {
  const [documentUrl, setDocumentUrl] = useState('');
  const [title, setTitle] = useState('');
  const [agency, setAgency] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!documentUrl.trim()) return;

    setIsSubmitting(true);
    try {
      const response = await fetch('/api/admin/policies', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'document',
          url: documentUrl,
          title: title || '공고문 정책',
          agency
        })
      });

      if (response.ok) {
        onSuccess();
        onClose();
        setDocumentUrl('');
        setTitle('');
        setAgency('');
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
    <Modal isOpen={isOpen} onClose={onClose} title="정책등록 (공고문)">
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">
            공고문 URL
          </label>
          <input
            type="url"
            value={documentUrl}
            onChange={(e) => setDocumentUrl(e.target.value)}
            className="w-full p-2 border rounded"
            placeholder="https://example.gov.kr/document.pdf"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            공고문 PDF 또는 문서 파일의 URL을 입력하세요.
          </p>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">
            정책명 (선택)
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full p-2 border rounded"
            placeholder="예: 청년창업지원사업"
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium mb-1">
            기관명 (선택)
          </label>
          <input
            type="text"
            value={agency}
            onChange={(e) => setAgency(e.target.value)}
            className="w-full p-2 border rounded"
            placeholder="예: 중소벤처기업부"
          />
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