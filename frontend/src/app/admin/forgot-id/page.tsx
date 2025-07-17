'use client';

import React, { useState } from 'react';
import Link from 'next/link';

export default function ForgotIdPage() {
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      const response = await fetch('/api/admin/forgot-id', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      if (response.ok) {
        setIsSuccess(true);
      } else {
        const data = await response.json();
        setError(data.error || '아이디 찾기 요청 중 오류가 발생했습니다.');
      }
    } catch (error) {
      setError('서버 연결 중 오류가 발생했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full p-6 bg-white rounded-lg shadow-md">
        <h1 className="text-2xl font-bold text-center mb-6">아이디 찾기</h1>

        {isSuccess ? (
          <div className="text-center">
            <div className="mb-4 text-green-600">
              아이디 정보가 이메일로 발송되었습니다.
            </div>
            <p className="mb-4 text-gray-600">
              이메일을 확인하여 아이디 정보를 확인하세요.
            </p>
            <Link href="/admin/login" className="text-blue-600 hover:underline">
              로그인 페이지로 돌아가기
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-1">이메일</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full p-2 border rounded"
                placeholder="관리자 이메일 주소"
                required
              />
              <p className="mt-1 text-xs text-gray-500">
                가입 시 사용한 이메일 주소를 입력하세요. 해당 이메일로 아이디 정보가 발송됩니다.
              </p>
            </div>

            {error && (
              <div className="mb-4 text-red-600 text-sm">{error}</div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {isSubmitting ? '처리 중...' : '아이디 찾기'}
            </button>

            <div className="mt-4 text-center">
              <Link href="/admin/login" className="text-blue-600 hover:underline text-sm">
                로그인 페이지로 돌아가기
              </Link>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}