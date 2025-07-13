'use client';
import {useState} from 'react';

export default function Profile() {
  const [complete] = useState(60); // 백엔드 값 연동
  return (
    <div className="max-w-md mx-auto p-8">
      <h1 className="text-xl font-bold mb-6">내 정보</h1>
      <div className="space-y-4">
        <div>
          <p className="text-sm mb-1">프로필 완성도 {complete}%</p>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-primary h-2 rounded-full" style={{width: `${complete}%`}} />
          </div>
        </div>

        <button className="btn-primary w-full">정보 추가하기</button>
        
        <div className="mt-6 space-y-3">
          <div className="flex justify-between text-sm">
            <span>연령대</span>
            <span className="text-gray-500">미입력</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>지역</span>
            <span className="text-gray-500">미입력</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>사업형태</span>
            <span className="text-gray-500">미입력</span>
          </div>
        </div>
      </div>
    </div>
  );
}