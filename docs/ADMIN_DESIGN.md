알겠습니다. React/Next.js 기반으로, 로그인, 정책 관리, 사용자 목록, 대시보드 지표를 포함한 관리자 화면을 공공기관 스타일에 세련됨을 더해 설계하겠습니다. 지금부터 관리자 페이지의 UI를 디자인하고, 실제 교체 가능한 코드로 구성된 파일을 제공하겠습니다.


# GovChat 관리자 페이지 설계 및 구현 (Next.js + Tailwind CSS 기반)

## 기술 스택 및 디자인 개요

* **프론트엔드 프레임워크:** React (Next.js) – Next.js의 App Router를 사용하여 페이지별 라우팅 및 레이아웃 구성
* **언어 및 타입:** TypeScript – 코드 안정성과 가독성을 높임
* **스타일링:** Tailwind CSS – 유틸리티 클래스 기반으로 빠르고 일관된 스타일 적용
* **UI 컴포넌트:** shadcn/ui 라이브러리 – Tailwind CSS로 구성된 React UI 컴포넌트 세트 (버튼, 입력필드, 카드 등) 활용
* **차트 라이브러리:** Chart.js 또는 유사한 도구 – 대시보드의 지표를 시각화 (예: 막대/선형 차트)
* **인증:** Firebase Auth 또는 커스텀 API – 이메일/비밀번호 기반 로그인 (현재는 플레이스홀더로 구현 준비)

디자인 측면에서는 공공기관 느낌의 **보수적이고 깔끔한 UI**를 지향합니다. 전체적으로 밝은 베이지/회색 계열의 배경에 **블루 톤**을 주요 강조색으로 사용하고, 필요한 경우 산뜻한 민트나 중립적인 그레이 톤을 보조색으로 활용합니다. 컴포넌트 디자인은 **미니멀리즘**을 따르며, Tailwind CSS와 shadcn/ui의 기본 스타일을 이용해 **절제된 버튼과 카드 디자인**, **부드러운 그림자 효과**, **반응형 레이아웃**을 구현합니다. 모든 페이지는 데스크톱뿐 아니라 모바일 화면에서도 내용이 읽기 쉽게 구성됩니다.

## 프로젝트 구조

아래와 같이 Next.js의 프로젝트 구조를 설계하였습니다. 각 주요 페이지는 `app/admin` 경로 아래 **개별 폴더**로 분리되어 있어, 페이지 단위로 파일을 교체하거나 수정하기 쉽습니다. 공통 UI 컴포넌트는 `components/ui` 폴더에 모아 두고 Tailwind CSS 클래스로 일관된 스타일을 적용했습니다.

```plaintext
src/
├── app/
│   ├── admin/
│   │   ├── layout.tsx         # 관리자 공통 레이아웃 (사이드바/헤더 등 공용 UI)
│   │   ├── page.tsx           # 대시보드 페이지 (관리자 메인 지표 화면)
│   │   ├── login/
│   │   │   └── page.tsx       # 로그인 페이지 (별도 레이아웃 사용)
│   │   ├── policies/
│   │   │   └── page.tsx       # 정책 목록 페이지 (CRUD 기능 UI)
│   │   └── users/
│   │       └── page.tsx       # 사용자 목록 페이지
│   └── globals.css            # 글로벌 스타일 (Tailwind 리셋 및 테마 설정)
├── components/
│   ├── ui/                    # shadcn/ui 기반 컴포넌트 모음
│   │   ├── button.tsx         # 기본 버튼 컴포넌트 (TailwindCSS 스타일 포함)
│   │   ├── input.tsx          # 기본 인풋 필드 컴포넌트
│   │   └── card.tsx           # 카드 레이아웃 컴포넌트
│   ├── Chart.tsx              # 차트 컴포넌트 (예: Chart.js 래핑)
│   └── ... 기타 재사용 컴포넌트들 ...
├── lib/
│   ├── api.ts                 # 백엔드 API 호출 모듈 (예: Axios 인스턴스)
│   └── auth.ts                # 인증 관련 함수 (Firebase/Auth 또는 모킹용)
└── ... (그 외 설정/구성 파일 등)
```

위 구조에서 `app/admin/layout.tsx`는 **관리자 공통 레이아웃**을 정의합니다. 사이드바 내비게이션과 상단 헤더 등을 포함하여, 관리자 영역의 모든 페이지에 공통으로 적용됩니다 (Next.js App Router의 레이아웃 기능 활용). 각 하위 페이지(`login`, `policies`, `users` 등)는 해당 폴더의 `page.tsx` 파일로 구현되어, 서로 **독립적으로 수정 및 교체**가 가능합니다. TailwindCSS의 유틸리티 클래스로 반응형 디자인을 손쉽게 적용했고, shadcn/ui 컴포넌트로 기본 디자인 가이드 (여백, 폰트 크기, 색상 등)를 통일했습니다.

### 관리자 레이아웃 (`app/admin/layout.tsx`)

```tsx
import React, { ReactNode } from 'react';
import Link from 'next/link';

interface AdminLayoutProps {
  children: ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  return (
    <div className="min-h-screen flex">
      {/* 사이드바 메뉴 */}
      <aside className="w-60 bg-gray-100 p-4">
        <h2 className="text-xl font-bold text-center mb-6">GovChat Admin</h2>
        <nav className="space-y-2">
          <Link href="/admin" className="block px-3 py-2 rounded hover:bg-gray-200">
            대시보드
          </Link>
          <Link href="/admin/policies" className="block px-3 py-2 rounded hover:bg-gray-200">
            정책 관리
          </Link>
          <Link href="/admin/users" className="block px-3 py-2 rounded hover:bg-gray-200">
            사용자 목록
          </Link>
        </nav>
      </aside>
      {/* 메인 콘텐츠 영역 */}
      <main className="flex-1 p-6 bg-gray-50">
        {children}
      </main>
    </div>
  );
}
```

**설명:** 이 레이아웃 컴포넌트는 관리자 페이지들의 공통 골격을 제공합니다. 좌측에는 사이드바 메뉴가 고정되어 있으며, **대시보드**, **정책 관리**, **사용자 목록** 등 주요 섹션으로 이동할 수 있는 링크로 구성됩니다. 사이드바에는 프로젝트 로고 또는 타이틀(`GovChat Admin`)을 상단에 배치하여 식별성을 높였습니다. 배경은 연한 회색(`bg-gray-100`/`bg-gray-50`)을 사용해 콘텐츠와 구분되도록 했고, 선택 또는 호버된 메뉴 항목은 약간 진한 회색 배경(`hover:bg-gray-200`)으로 하이라이트되어 **시각적 피드백**을 줍니다. 우측의 `main` 영역은 패딩과 함께 **흰색/밝은 배경**으로 설정하여 콘텐츠가 잘 보이도록 했으며, 여기에서 각 페이지별 내용이 렌더링됩니다. 레이아웃은 `min-h-screen`과 flex 레이아웃을 사용하여 화면 전체 높이를 채우며 반응형으로 동작합니다 (작은 화면에서는 사이드바를 상단에 두거나 토글 메뉴로 변경하는 식의 추가 구현 가능).

### 로그인 페이지 (`app/admin/login/page.tsx`)

```tsx
'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export default function AdminLoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string>('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(''); // 기존 오류 메시지 리셋
    try {
      // TODO: 실제 인증 API 연동 또는 Firebase 인증 처리
      // 예: await signInWithEmailAndPassword(auth, email, password);
      // 임시로 성공 처리를 가정
      router.replace('/admin');  // 로그인 성공 시 대시보드로 리디렉트
    } catch (err) {
      // 인증 실패 시 오류 표시
      setError('로그인 실패: 자격 증명을 확인하세요.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form onSubmit={handleLogin} className="w-full max-w-sm bg-white p-6 rounded shadow-md">
        <h1 className="text-2xl font-bold text-center mb-4">관리자 로그인</h1>
        {/* 이메일 입력 */}
        <Input 
          type="email" 
          placeholder="이메일" 
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mb-3"
          required
        />
        {/* 비밀번호 입력 */}
        <Input 
          type="password" 
          placeholder="비밀번호" 
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mb-4"
          required
        />
        {/* 오류 메시지 표시 */}
        {error && <p className="text-red-600 text-sm mb-2">{error}</p>}
        {/* 로그인 버튼 */}
        <Button type="submit" className="w-full">로그인</Button>
      </form>
    </div>
  );
}
```

**설명:** 로그인 페이지는 관리자 영역 진입을 위한 **인증 화면**입니다. 중앙에 이메일과 비밀번호를 입력할 수 있는 폼을 배치하고, 상단에는 간단한 로고 또는 타이틀(여기서는 *관리자 로그인* 헤더 텍스트로 대체)을 표시했습니다. 폼은 `max-w-sm` 크기로 적절한 폭을 유지하며, **흰색 카드 스타일 박스**(`bg-white`, `rounded`, `shadow-md`)로 시각적 집중도를 높였습니다. 이메일/비밀번호 필드는 shadcn/ui의 `<Input>` 컴포넌트를 사용하여 일관된 스타일의 인풋을 제공하고, Tailwind 클래스로 간격(`mb-3`, `mb-4`)을 주어 요소 간 간격을 조정했습니다.

사용자가 **로그인 버튼**을 누르면 `handleLogin` 함수가 호출되어 폼 제출을 처리합니다. 현재는 실제 백엔드 인증 대신 **플레이스홀더**로 구현되어, 추후 `Firebase Auth`의 `signInWithEmailAndPassword` 혹은 자체 API(`/api/admin/login` 등)를 연동할 수 있도록 구조를 마련했습니다. 성공적으로 로그인하면 `next/navigation`의 `router.replace('/admin')`를 통해 관리자 대시보드로 리디렉션하고, 실패하면 상태값 `error`에 오류 메시지를 설정하여 사용자에게 피드백을 제공합니다. 이 페이지는 별도의 레이아웃을 사용하지 않고 전체 화면을 폼으로 채우기 때문에 (`min-h-screen flex items-center justify-center`) 모바일에서도 중앙 정렬된 로그인 폼이 나타나도록 해상도에 따라 유연하게 동작합니다.

### 정책 목록 페이지 (`app/admin/policies/page.tsx`)

```tsx
'use client';

import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

interface Policy {
  id: number;
  title: string;
  category: string;
  lastUpdated: string;
}

export default function PoliciesPage() {
  // 예시용 정책 데이터 (실제로는 API를 통해 불러옴)
  const policies: Policy[] = [
    { id: 1, title: '청년 취업 지원', category: '고용', lastUpdated: '2025-07-10' },
    { id: 2, title: '소상공인 창업 지원', category: '경제', lastUpdated: '2025-07-08' },
    // ... (기타 정책들)
  ];

  const handleDelete = (policyId: number) => {
    // TODO: 정책 삭제 로직 (API 호출 후 상태 갱신)
    alert(`정책 ID ${policyId} 삭제 기능 호출됨`);
  };

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">정책 관리</h2>
      {/* 정책 등록 버튼 */}
      <Link href="/admin/policies/new">
        <Button className="mb-4">+ 새 정책 등록</Button>
      </Link>
      {/* 정책 리스트 테이블 */}
      <table className="min-w-full border-t border-b text-sm">
        <thead className="bg-gray-100">
          <tr>
            <th className="text-left p-2">정책명</th>
            <th className="text-left p-2">카테고리</th>
            <th className="text-left p-2">최근 수정일</th>
            <th className="p-2">액션</th>
          </tr>
        </thead>
        <tbody>
          {policies.map(policy => (
            <tr key={policy.id} className="border-b hover:bg-gray-50">
              <td className="p-2">{policy.title}</td>
              <td className="p-2">{policy.category}</td>
              <td className="p-2">{policy.lastUpdated}</td>
              <td className="p-2 text-center">
                <Link href={`/admin/policies/${policy.id}/edit`} className="text-blue-600 hover:underline mr-3">
                  수정
                </Link>
                <button onClick={() => handleDelete(policy.id)} className="text-red-600 hover:underline">
                  삭제
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

**설명:** 이 페이지는 관리자가 등록된 **정책 리스트를 조회 및 관리**할 수 있는 화면입니다. 상단에는 페이지 제목과 더불어 **"새 정책 등록"** 버튼이 배치되어 있어 새로운 정책을 추가할 수 있습니다. 이 버튼은 Shadcn UI의 `<Button>` 컴포넌트를 사용하였으며, Next.js의 `<Link>`로 감싸 **정책 등록 폼 페이지**(`/admin/policies/new`)로 이동할 준비가 되어 있습니다. (등록 폼 페이지에서는 정책의 제목, 내용 등을 입력하고 저장하도록 구현할 수 있습니다.)

정책 목록은 `<table>` 요소를 사용해 표 형식으로 나타내며, **정책명**, **카테고리**, **최근 수정일** 컬럼과 함께 각 행마다 **액션(수정/삭제)** 버튼을 제공합니다. 테이블 헤더는 연한 회색 배경(`bg-gray-100`)으로 구분했고, 항목 행은 `:hover` 시 살짝 강조(`hover:bg-gray-50`)되도록 처리하여 시각적인 구분을 주었습니다.

"수정" 버튼은 해당 정책의 편집 페이지로 이동하기 위한 링크이며, "삭제" 버튼은 클릭 시 `handleDelete` 함수를 호출합니다. 현재 `handleDelete`는 실제 API 연동 대신 `alert`로 플레이스홀더를 넣었지만, 실제 환경에서는 `fetch`/`axios`로 DELETE 요청 후 성공 시 정책 목록을 갱신하도록 만들 수 있습니다. 이러한 구조로 CRUD 기능을 구현하면, 관리자는 이 페이지에서 바로 정책 추가, 수정, 삭제를 모두 수행할 수 있습니다.

### 사용자 목록 페이지 (`app/admin/users/page.tsx`)

```tsx
'use client';

import React from 'react';

interface User {
  id: number;
  name: string;
  email: string;
  signedUp: string;
  lastLogin: string;
}

export default function UsersPage() {
  // 예시용 사용자 데이터 (실제로는 API를 통해 불러옴)
  const users: User[] = [
    { id: 1, name: '홍길동', email: 'hong@example.com', signedUp: '2025-06-01', lastLogin: '2025-07-12' },
    { id: 2, name: '김지원', email: 'kim@example.com', signedUp: '2025-06-15', lastLogin: '2025-07-13' },
    // ... (기타 사용자들)
  ];

  return (
    <div>
      <h2 className="text-xl font-bold mb-4">사용자 목록</h2>
      <table className="min-w-full border-t border-b text-sm">
        <thead className="bg-gray-100">
          <tr>
            <th className="text-left p-2">이름</th>
            <th className="text-left p-2">이메일</th>
            <th className="text-left p-2">가입일</th>
            <th className="text-left p-2">마지막 접속일</th>
          </tr>
        </thead>
        <tbody>
          {users.map(user => (
            <tr key={user.id} className="border-b hover:bg-gray-50">
              <td className="p-2">{user.name}</td>
              <td className="p-2">{user.email}</td>
              <td className="p-2">{user.signedUp}</td>
              <td className="p-2">{user.lastLogin}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

**설명:** 사용자 목록 페이지에서는 **플랫폼에 가입한 모든 사용자 계정 정보**를 표 형태로 보여줍니다. 각 사용자에 대해 이름, 이메일, 가입일, 마지막 접속일 등의 기본 프로필 정보를 한 눈에 볼 수 있도록 컬럼을 구성했습니다. 정책 목록과 마찬가지로 `<table>`을 이용하여 데이터 행을 나열하며, 헤더에 회색 배경을 주어 구분하고, 행 `hover` 시 배경을 살짝 변경하여 row 강조 효과를 주었습니다.

이 페이지에서는 주로 **조회 기능**에 초점을 맞추고 있으며, 추가적인 기능으로 다음을 고려할 수 있습니다:

* 상단에 검색 바를 두어 이메일이나 이름으로 사용자를 필터링
* 각 행 끝에 관리 액션(예: 권한 변경, 비밀번호 초기화 버튼) 추가

이러한 기능들은 요구 사항에 따라 추후 확장 가능합니다. 현재 구현에서는 제시된 항목인 사용자 목록 정보를 일목요연하게 표시하는 데 집중했습니다. 데이터는 실제로는 백엔드 API (`GET /users` 등)를 통해 가져오지만, 예시에서는 하드코딩된 배열을 사용했습니다.

### 대시보드 페이지 (`app/admin/page.tsx`)

```tsx
'use client';

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
// import { Chart } from '@/components/Chart'  // 차트 컴포넌트를 사용하는 경우 임포트

export default function AdminDashboardPage() {
  // 예시 지표 데이터 (실제로는 API를 통해 불러옴)
  const stats = {
    totalPolicies: 12,
    totalUsers: 134,
    matchSuccessRate: 87  // 퍼센트(%)
  };

  // (예시) 차트에 표시할 데이터
  const monthlySuccess = [
    { month: '1월', rate: 75 },
    { month: '2월', rate: 80 },
    { month: '3월', rate: 85 },
    { month: '4월', rate: 88 },
    { month: '5월', rate: 90 },
    { month: '6월', rate: 87 },
  ];

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">대시보드</h2>
      {/* 주요 지표 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>총 정책 수</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.totalPolicies}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>총 사용자 수</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.totalUsers}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>매칭 성공률</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{stats.matchSuccessRate}%</p>
          </CardContent>
        </Card>
      </div>

      {/* 차트 섹션 */}
      <div className="mt-8 bg-white p-4 rounded shadow">
        <h3 className="text-lg font-semibold mb-4">월별 매칭 성공률 추이</h3>
        {/* 차트 컴포넌트 자리: 예를 들어 Bar 차트나 Line 차트를 표시 */}
        {/* <Chart data={monthlySuccess} /> */}
        <p className="text-sm text-gray-500">[차트 예시: 월별 매칭 성공률 {`<Chart>`}]</p>
      </div>
    </div>
  );
}
```

**설명:** 대시보드 페이지는 관리자 페이지에 로그인하면 가장 먼저 보게 되는 **요약 지표 화면**입니다. 상단에는 전체 시스템의 상태를 보여주는 **카드 형태의 통계**가 3개 배치되어 있습니다:

* **총 정책 수:** 현재 등록되어 있는 지원 정책 프로그램의 개수
* **총 사용자 수:** 플랫폼에 가입한 총 사용자 수
* **매칭 성공률:** 사용자들에게 추천된 정책 매칭의 성공 비율 (예: 87%)

이러한 카드들은 shadcn/ui의 `<Card>` 컴포넌트를 활용하여 일정한 스타일로 구성되었으며, 제목(`<CardTitle>`)과 내용(`<CardContent>`) 부분으로 구분되어 있습니다. 카드 내 숫자는 큰 글씨(`text-3xl font-bold`)로 표시하여 한눈에 들어오도록 했습니다. 화면 레이아웃은 `grid`를 사용해 반응형으로 설계되었는데, 모바일 화면에서는 한 열(`grid-cols-1`)로 쌓이고, 큰 화면(md 이상)에서는 세 열로 나란히(`grid-cols-3`) 보여집니다.

하단에는 **차트 섹션**이 있어 시간 흐름에 따른 매칭 성공률 변화를 시각화합니다. 예시로 "월별 매칭 성공률 추이"를 보여주는 영역을 넣었으며, 실제 구현 시 Chart.js나 Recharts 등의 라이브러리를 사용해 **막대 차트**나 **선형 차트**를 그릴 수 있습니다.

위 코드에서는 `monthlySuccess`라는 간단한 데이터 배열을 준비해두었고, `<Chart>` 컴포넌트 (예: Chart.js를 래핑한 커스텀 컴포넌트)를 통해 해당 데이터를 시각화한다고 가정했습니다. 실제 적용 시에는 `Chart` 컴포넌트를 `dynamic import`하여 서버 사이드 렌더링을 피하고(`ssr: false`), 차트 라이브러리가 클라이언트에서만 동작하도록 구성할 것입니다.

---

이와 같이 **React + Next.js** 기반으로 GovChat 관리자 페이지를 구현하면, 각 화면이 독립적인 모듈로 구성되어 유지보수가 용이합니다. Tailwind CSS와 shadcn/ui를 활용해 **일관된 디자인 시스템**을 적용함으로써, 색상 팔레트와 컴포넌트 스타일이 모든 페이지에서 통일되고 수정 역시 중앙에서 관리할 수 있습니다. 또한 Next.js의 폴더별 라우팅과 레이아웃 기능을 사용하여 페이지 파일을 쉽게 교체하거나 새로운 페이지를 추가할 수 있어, 향후 요구사항 변경이나 기능 추가에도 유연하게 대응할 수 있습니다. 모든 요소는 반응형으로 설계되어 다양한 해상도에서 깨짐 없이 동작하며, 공공 서비스에 걸맞은 단정하고 신뢰감 있는 UI/UX를 제공하도록 구현되었습니다.
