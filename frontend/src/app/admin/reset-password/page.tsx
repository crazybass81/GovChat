'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';

export default function ResetPasswordPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');
  const [tokenValid, setTokenValid] = useState<boolean | null>(null);
  const [tokenChecking, setTokenChecking] = useState(true);

  useEffect(() => {
    // 토큰 유효성 검증
    if (token) {
      validateToken();
    } else {
      setTokenValid(false);
      setTokenChecking(false);
      setError('유효하지 않은 접근입니다. 비밀번호 재설정 링크가 필요합니다.');
    }
  }, [token]);

  const validateToken = async () => {
    try {
      const response = await fetch(`/api/admin/reset-password?token=${token}`);
      if (response.ok) {
        setTokenValid(true);
      } else {
        const data = await response.json();
        setTokenValid(false);
        setError(data.error || '유효하지 않은 토큰입니다.');
      }
    } catch (error) {
      setTokenValid(false);
      setError('토큰 검증 중 오류가 발생했습니다.');
    } finally {
      setTokenChecking(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // 비밀번호 유효성 검증
    if (password.length < 8) {
      setError('비밀번호는 최소 8자 이상이어야 합니다.');
      return;
    }

    if (password !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.');
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch('/api/admin/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, password })
      });

      if (response.ok) {
        setIsSuccess(true);
      } else {
        const data = await response.json();
        setError(data.error || '비밀번호 재설정 중 오류가 발생했습니다.');
      }
    } catch (error) {
      setError('서버 연결 중 오류가 발생했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (tokenChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full p-6 bg-white rounded-lg shadow-md">
          <div className="text-center">토큰 검증 중...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full p-6 bg-white rounded-lg shadow-md">
        <h1 className="text-2xl font-bold text-center mb-6">비밀번호 재설정</h1>

        {!tokenValid ? (
          <div className="text-center">
            <div className="mb-4 text-red-600">{error}</div>
            <Link href="/admin/forgot-password" className="text-blue-600 hover:underline">
              비밀번호 재설정 다시 요청하기
            </Link>
          </div>
        ) : isSuccess ? (
          <div className="text-center">
            <div className="mb-4 text-green-600">
              비밀번호가 성공적으로 재설정되었습니다.
            </div>
            <p className="mb-4 text-gray-600">
              이제 새 비밀번호로 로그인할 수 있습니다.
            </p>
            <Link href="/admin/login" className="text-blue-600 hover:underline">
              로그인 페이지로 이동
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-sm font-medium mb-1">새 비밀번호</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full p-2 border rounded"
                placeholder="최소 8자 이상"
                required
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium mb-1">비밀번호 확인</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full p-2 border rounded"
                placeholder="비밀번호 다시 입력"
                required
              />
            </div>

            {error && (
              <div className="mb-4 text-red-600 text-sm">{error}</div>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {isSubmitting ? '처리 중...' : '비밀번호 재설정'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}