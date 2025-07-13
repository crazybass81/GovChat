'use client';

import { useSession, signOut } from 'next-auth/react';
import Link from 'next/link';
import { useState } from 'react';

export default function AuthNavigation() {
  const { data: session, status } = useSession();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  if (status === 'loading') {
    return (
      <div className="animate-pulse">
        <div className="h-8 w-16 bg-gray-200 rounded"></div>
      </div>
    );
  }

  if (!session) {
    return (
      <Link
        href="/auth/signin"
        className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
      >
        로그인
      </Link>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        className="flex items-center space-x-2 text-sm font-medium text-gray-700 hover:text-gray-900 focus:outline-none"
      >
        {session.user?.image ? (
          <img
            className="h-8 w-8 rounded-full"
            src={session.user.image}
            alt={session.user.name || '사용자'}
          />
        ) : (
          <div className="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center">
            <span className="text-white text-sm font-medium">
              {session.user?.name?.charAt(0) || session.user?.email?.charAt(0) || 'U'}
            </span>
          </div>
        )}
        <span className="hidden md:block">
          {session.user?.name || session.user?.email}
        </span>
        <svg
          className={`h-4 w-4 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isDropdownOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50 border">
          <div className="px-4 py-2 text-sm text-gray-700 border-b">
            <p className="font-medium">{session.user?.name}</p>
            <p className="text-gray-500">{session.user?.email}</p>
            {session.provider && (
              <p className="text-xs text-gray-400 mt-1">
                {session.provider} 계정
              </p>
            )}
          </div>
          
          <Link
            href="/user/profile"
            className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
            onClick={() => setIsDropdownOpen(false)}
          >
            프로필 설정
          </Link>
          
          <Link
            href="/user/settings"
            className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
            onClick={() => setIsDropdownOpen(false)}
          >
            계정 설정
          </Link>
          
          <button
            onClick={() => {
              setIsDropdownOpen(false);
              signOut({ callbackUrl: '/auth/signin' });
            }}
            className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
          >
            로그아웃
          </button>
        </div>
      )}

      {/* 드롭다운 외부 클릭 시 닫기 */}
      {isDropdownOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsDropdownOpen(false)}
        />
      )}
    </div>
  );
}