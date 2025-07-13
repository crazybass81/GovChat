'use client';
import { useState } from 'react';

const steps = ['개인 정보', '사업 정보', '알림 설정'];

function PersonalForm() {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">개인 정보</h2>
      <input className="w-full rounded-md border p-3" placeholder="이름" />
      <input className="w-full rounded-md border p-3" placeholder="나이" />
      <select className="w-full rounded-md border p-3">
        <option>거주 지역 선택</option>
        <option>서울</option>
        <option>경기</option>
      </select>
    </div>
  );
}

function BusinessForm() {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">사업 정보</h2>
      <select className="w-full rounded-md border p-3">
        <option>업종 선택</option>
        <option>제조업</option>
        <option>서비스업</option>
      </select>
      <input className="w-full rounded-md border p-3" placeholder="사업자등록번호" />
    </div>
  );
}

function NotifyForm() {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">알림 설정</h2>
      <label className="flex items-center gap-2">
        <input type="checkbox" />
        <span>이메일 알림 받기</span>
      </label>
      <label className="flex items-center gap-2">
        <input type="checkbox" />
        <span>SMS 알림 받기</span>
      </label>
    </div>
  );
}

export default function Onboarding() {
  const [active, setActive] = useState(0);

  return (
    <div className="mx-auto max-w-xl py-16">
      {/* Stepper */}
      <div className="mb-8 flex justify-between">
        {steps.map((label, i) => (
          <div key={label} className="flex items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              i <= active ? 'bg-primary text-white' : 'bg-gray-200 text-gray-600'
            }`}>
              {i + 1}
            </div>
            <span className="ml-2 text-sm">{label}</span>
            {i < steps.length - 1 && <div className="w-12 h-px bg-gray-300 mx-4" />}
          </div>
        ))}
      </div>

      {active === 0 && <PersonalForm />}
      {active === 1 && <BusinessForm />}
      {active === 2 && <NotifyForm />}

      <div className="mt-8 flex justify-between">
        <button
          className="px-4 py-2 text-gray-600 hover:text-gray-800"
          disabled={active === 0}
          onClick={() => setActive(a => a - 1)}>
          이전
        </button>
        <button
          className="px-6 py-2 bg-primary text-white rounded-md hover:bg-blue-700"
          onClick={() => setActive(a => Math.min(a + 1, 2))}>
          {active === 2 ? '완료' : '다음'}
        </button>
      </div>
    </div>
  );
}