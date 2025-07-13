# GovChat Frontend

정부지원사업 맞춤 매칭 챗봇의 프론트엔드 애플리케이션입니다.

## 기술 스택

- **Next.js 14** - React 프레임워크
- **TypeScript** - 타입 안전성
- **Tailwind CSS** - 스타일링
- **Heroicons** - 아이콘
- **Axios** - HTTP 클라이언트

## 주요 기능

### 사용자 기능
- **AI 챗봇 상담**: 대화형 인터페이스로 맞춤 정책 추천
- **프로필 완성도**: 실시간 정보 수집 진행률 표시
- **반응형 디자인**: 모바일 우선 설계

### 관리자 기능
- **정책 관리**: CRUD 작업 (생성, 읽기, 수정, 삭제)
- **정책 발행**: 초안 → 발행 상태 관리
- **YAML 편집기**: 정책 설정 직접 편집

## 설치 및 실행

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build
npm start
```

## 환경 변수

```bash
NEXT_PUBLIC_API_BASE=https://your-api-gateway-url/prod
```

## 프로젝트 구조

```
src/
├── app/                 # Next.js App Router
│   ├── user/chat/      # 사용자 채팅 페이지
│   ├── admin/policies/ # 관리자 정책 관리
│   └── globals.css     # 글로벌 스타일
├── components/         # 재사용 가능한 컴포넌트
├── hooks/             # 커스텀 React 훅
│   └── useChat.ts     # 채팅 상태 관리
└── lib/               # 유틸리티 및 API
    └── api.ts         # API 클라이언트
```

## API 연동

백엔드 API와의 연동을 위해 다음 엔드포인트를 사용합니다:

- `POST /chat` - 채팅 메시지 전송
- `POST /question` - 후속 질문 생성
- `GET /policies` - 정책 목록 조회
- `POST /policies` - 새 정책 생성
- `PUT /policies/{id}` - 정책 수정
- `POST /policies/{id}:publish` - 정책 발행

## 성능 최적화

- **코드 분할**: Next.js 자동 코드 분할
- **이미지 최적화**: Next.js Image 컴포넌트
- **번들 분석**: `npm run analyze`로 번들 크기 확인

## 접근성 (A11y)

- WCAG 2.1 AA 준수
- 키보드 네비게이션 지원
- 스크린 리더 호환성
- 색상 대비 4.5:1 이상

## 배포

Vercel, Netlify, 또는 AWS Amplify에서 배포 가능합니다.

```bash
# Vercel 배포
npx vercel

# 정적 빌드 (필요시)
npm run build
npm run export
```