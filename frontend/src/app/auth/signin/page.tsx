'use client';
import { signIn } from 'next-auth/react';
import Image from 'next/image';

export default function SignIn() {
  const providers = [
    { id: 'kakao', label: 'Continue with Kakao', logo: '/icons/kakao.svg' },
    { id: 'google', label: 'Continue with Google', logo: '/icons/google.svg' },
    { id: 'naver', label: 'Continue with Naver', logo: '/icons/naver.svg' },
  ];

  return (
    <div className="mx-auto max-w-sm py-20 space-y-10">
      <h1 className="text-center text-2xl font-semibold">로그인 / 회원가입</h1>

      {providers.map(p => (
        <button
          key={p.id}
          onClick={() => signIn(p.id, { callbackUrl: '/chat' })}
          className="flex w-full items-center justify-center gap-3 rounded-md bg-white py-3 shadow hover:bg-gray-50">
          <div className="w-6 h-6 bg-gray-200 rounded" />
          <span className="text-sm font-medium text-gray-700">{p.label}</span>
        </button>
      ))}

      <div className="text-center text-xs text-gray-400">
        By continuing, you agree to our&nbsp;
        <a href="/terms" className="underline">
          Terms
        </a>
        .
      </div>
    </div>
  );
}