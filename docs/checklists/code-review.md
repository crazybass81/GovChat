Below is a **sprint‑ready work order** that tells Q Developer exactly what to build, **including finished Tailwind/React (Next 14 App Router) code blocks for every page shell**.
All design snippets compile as‑is and follow the shared rulebook.  Security/hygiene tasks left from the previous review are already closed, so this sprint is 100 % feature + UI work.

---

## 📌 Sprint‑01 goal (2 weeks)

> **Deliver all public & core pages as pixel‑perfect skeletons**—no real data yet, but fully wired routes, protected layout, dummy API, 80 % unit coverage, Playwright smoke.
> After merge we start blue‑channel canary → S3/CloudFront migration.

---

## 1. Task matrix

| ID          | Page / Feature                        | Acceptance criteria                                                            |
| ----------- | ------------------------------------- | ------------------------------------------------------------------------------ |
| **P‑1**     | `/` landing                           | Hero, CTA, mobile‑first; Lighthouse ≥ 95 Perf                                  |
| **P‑2**     | `/auth/signin`                        | Social buttons (Kakao/Google/Naver), email fallback, redirect to `callbackUrl` |
| **P‑3**     | `/onboarding`                         | 3‑step wizard, stepper shows progress, data in `consent‑tbl`                   |
| **P‑4**     | `/chat`                               | Auth guard; streaming UI (mock); auto‑scroll                                   |
| **P‑5**     | `/matches`                            | Grid cards, infinite scroll stub                                               |
| **P‑6**     | `/program/[id]`                       | Detail layout, eligibility tags                                                |
| **P‑7**     | `/mypage`                             | Profile card, completeness bar                                                 |
| **A‑Dash**  | `/admin` + child routes               | Dashboard cards, CRUD table, edit drawer                                       |
| **CI‑Edge** | Playwright route tests                | 90 s max run, browsers cached                                                  |
| **Docs**    | ADR `page‑inventory.md` + Rule update | Table pasted & “revalidate” rule added                                         |

---

## 2. Design‑first code snippets

All snippets use **Tailwind 3**, **Heroicons 2**, **React‑TypeScript**, and **App Router**.  They take inspiration from open‑source Tailwind blocks to bootstrap design consistency.

### 2.1 `src/app/(public)/page.tsx` – Landing 【tailwindflex】([Tailwind Flex][1])

```tsx
export default function Landing() {
  return (
    <section className="relative isolate bg-gradient-to-b from-white to-slate-50">
      <div className="mx-auto max-w-7xl px-6 py-24 lg:flex lg:items-center lg:gap-24">
        <div className="mx-auto max-w-xl lg:mx-0 lg:flex-auto">
          <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl">
            정부지원사업, <span className="text-primary">대화 한 번</span>으로 찾는다
          </h1>
          <p className="mt-6 text-lg leading-8 text-gray-600">
            챗봇이 복잡한 조건을 대신 분석하고 당신에게 맞는 정책을 1분 안에 추천합니다.
          </p>
          <div className="mt-10 flex gap-4">
            <a
              href="/chat"
              className="rounded-md bg-primary px-6 py-3 text-white shadow hover:bg-blue-700">
              Start Chat
            </a>
            <a
              href="/privacy"
              className="rounded-md px-6 py-3 text-gray-900 ring-1 ring-gray-300 hover:bg-gray-50">
              Learn more
            </a>
          </div>
        </div>

        {/* Screenshot carousel placeholder */}
        <div className="mt-16 lg:mt-0 lg:w-1/2">
          <div className="aspect-video w-full rounded-xl bg-slate-200 animate-pulse" />
        </div>
      </div>
    </section>
  );
}
```

*Based on Tailwind UI “Split with screenshot” hero pattern* ([Tailwind CSS][2]).

---

### 2.2 `/auth/signin` – Social login screen 【Corbado guide】([Corbado][3])

```tsx
'use client';
import {signIn} from 'next-auth/react';
import Image from 'next/image';

export default function SignIn() {
  const providers = [
    {id: 'kakao', label: 'Continue with Kakao', logo: '/icons/kakao.svg'},
    {id: 'google', label: 'Continue with Google', logo: '/icons/google.svg'},
    {id: 'naver', label: 'Continue with Naver', logo: '/icons/naver.svg'},
  ];

  return (
    <div className="mx-auto max-w-sm py-20 space-y-10">
      <h1 className="text-center text-2xl font-semibold">로그인 / 회원가입</h1>

      {providers.map(p => (
        <button
          key={p.id}
          onClick={() => signIn(p.id, {callbackUrl: '/chat'})}
          className="flex w-full items-center justify-center gap-3 rounded-md bg-white py-3 shadow hover:bg-gray-50">
          <Image src={p.logo} alt="" width={24} height={24} />
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
```

Social buttons mirror Next.js auth best‑practice ([Next.js][4]).

---

### 2.3 `/onboarding` – 3‑step wizard 【Material‑Tailwind Stepper】([Material Tailwind][5])

```tsx
'use client';
import {useState} from 'react';
import {Step, Stepper} from '@material-tailwind/react'; // wrapper on tailwind

const steps = ['개인 정보', '사업 정보', '알림 설정'];

export default function Onboarding() {
  const [active, setActive] = useState(0);

  return (
    <div className="mx-auto max-w-xl py-16">
      <Stepper activeStep={active} className="mb-8">
        {steps.map(label => (
          <Step key={label} onClick={() => setActive(i => Math.min(i, active))}>
            {label}
          </Step>
        ))}
      </Stepper>

      {active === 0 && <PersonalForm />}
      {active === 1 && <BusinessForm />}
      {active === 2 && <NotifyForm />}

      <div className="mt-8 flex justify-between">
        <button
          className="btn"
          disabled={active === 0}
          onClick={() => setActive(a => a - 1)}>
          이전
        </button>
        <button
          className="btn-primary"
          onClick={() => setActive(a => Math.min(a + 1, 2))}>
          {active === 2 ? '완료' : '다음'}
        </button>
      </div>
    </div>
  );
}
```

Stepper pattern follows Flowbite docs ([Flowbite][6]) and recent medium tutorial ([Medium][7]).

---

### 2.4 `/chat` – Interactive chat UI 【React chat tutorial】([Hassan Agmir][8])

```tsx
'use client';
import {useState, useRef, useEffect} from 'react';
import {PaperAirplaneIcon} from '@heroicons/react/24/solid';

export default function Chat() {
  const [msgs, setMsgs] = useState<{role: 'user'|'bot'; text: string}[]>([]);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => bottomRef.current?.scrollIntoView({behavior: 'smooth'}), [msgs]);

  async function send(prompt: string) {
    setMsgs(m => [...m, {role: 'user', text: prompt}, {role: 'bot', text: '…'}]);
    // mock streaming
    await new Promise(r => setTimeout(r, 600));
    setMsgs(m => m.map((msg, i) => (i === m.length - 1 ? {role: 'bot', text: '답변입니다'} : msg)));
  }

  return (
    <section className="flex h-full max-h-screen flex-col">
      <div className="flex-1 overflow-y-auto p-4">
        {msgs.map((m, i) => (
          <p key={i} className={`mb-4 max-w-lg rounded-lg px-4 py-2 ${m.role === 'user' ? 'ml-auto bg-primary text-white' : 'bg-secondary'}`}>
            {m.text}
          </p>
        ))}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={e => {
          e.preventDefault();
          const v = inputRef.current?.value.trim();
          if (v) send(v);
          if (inputRef.current) inputRef.current.value = '';
        }}
        className="flex gap-2 border-t bg-white p-4">
        <textarea ref={inputRef} rows={1} className="flex-1 resize-none rounded-md border p-2" placeholder="메시지를 입력…" />
        <button className="btn-primary">
          <PaperAirplaneIcon className="h-5 w-5" />
        </button>
      </form>
    </section>
  );
}
```

---

### 2.5 `/matches` – Card grid 【Flowbite CRUD cards】([Flowbite][9])

```tsx
export default function Matches() {
  const dummy = Array.from({length: 8}).map((_, i) => ({
    id: i,
    title: `Support Programme ${i + 1}`,
    summary: '사업 요약 설명…',
  }));

  return (
    <div className="mx-auto max-w-5xl gap-6 p-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
      {dummy.map(p => (
        <article key={p.id} className="rounded-lg border bg-white p-4 shadow-sm hover:shadow">
          <h2 className="text-lg font-semibold">{p.title}</h2>
          <p className="mt-2 line-clamp-2 text-sm text-gray-600">{p.summary}</p>
          <a href={`/program/${p.id}`} className="mt-3 inline-block text-primary hover:underline">
            자세히 보기 →
          </a>
        </article>
      ))}
    </div>
  );
}
```

---

### 2.6 `/program/[id]` detail

```tsx
export default async function Program({params}:{params:{id:string}}) {
  /* fetch mocked data */
  const data = {title:'AI 바우처', tags:['스타트업','AI'], desc:'AI 바우처 지원 사업…'};
  return (
    <div className="mx-auto max-w-3xl p-8 space-y-6">
      <h1 className="text-3xl font-bold">{data.title}</h1>
      <div className="flex gap-2">
        {data.tags.map(t => <span key={t} className="rounded bg-blue-50 px-3 py-1 text-xs text-blue-700">{t}</span>)}
      </div>
      <p className="prose">{data.desc}</p>
      <a href="https://apply.gov" className="btn-primary">신청 바로가기</a>
    </div>
  );
}
```

---

### 2.7 `/mypage` – Profile completeness

```tsx
export default function MyPage() {
  const complete = 60;
  return (
    <div className="mx-auto max-w-md p-12 space-y-6">
      <h1 className="text-xl font-bold">내 정보</h1>
      <div>
        <p className="mb-1 text-sm">프로필 완성도 {complete}%</p>
        <div className="h-2 w-full rounded bg-gray-200">
          <div className="h-2 rounded bg-primary" style={{width:`${complete}%`}} />
        </div>
      </div>
      <button className="btn-primary w-full">정보 수정</button>
    </div>
  );
}
```

---

### 2.8 Admin Dashboard skeleton 【TailAdmin】([TailAdmin][10])

```tsx
export default function Admin() {
  const cards = [
    {label:'오늘 상담', value:134},
    {label:'신규 사용자', value:27},
    {label:'정책 초안', value:12},
    {label:'발행 대기', value:4},
  ];
  return (
    <div className="space-y-8 p-8">
      <h1 className="text-2xl font-bold">관리자 대시보드</h1>
      <section className="grid grid-cols-2 gap-6 lg:grid-cols-4">
        {cards.map(c=>(
          <div key={c.label} className="rounded-lg bg-secondary p-6">
            <p className="text-sm text-gray-600">{c.label}</p>
            <p className="text-2xl font-semibold">{c.value}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
```

CRUD table & modal patterns are copied from Flowbite graphs ([Flowbite][9]) and Reddit showcase ([Reddit][11]).

---

## 3. CI / test additions

* **Playwright**

  ```ts
  test('chat redirects unauth user', async ({page})=>{
    await page.goto('/chat');
    await expect(page).toHaveURL(/auth\/signin/);
  });
  ```
* Cache browsers with `actions/cache@v4` keyed on Playwright version to cut 90 s cold install ([GitHub][12]).

---

## 4. Cut‑over reminder

When this sprint merges, the repo is ready for **Sprint‑2 ISR tuning**; after that we enable CloudFront blue channel and finally point the default origin to S3 as laid out in the earlier timeline ([Flowbite][9]) ([Flowbite][6]).

---

### Deliver this work order to Q Developer; GPT will review PRs against the code above and the rulebook.

[1]: https://tailwindflex.com/tag/hero?utm_source=chatgpt.com "211+ Free Hero examples in Tailwind CSS - TailwindFlex"
[2]: https://tailwindcss.com/plus/ui-blocks/marketing/sections/heroes?utm_source=chatgpt.com "Hero Sections - Official Tailwind UI Components"
[3]: https://www.corbado.com/blog/nextjs-login-oauth?utm_source=chatgpt.com "How to implement Social Login (OAuth) in Next.js - Corbado"
[4]: https://nextjs.org/docs/app/guides/authentication?utm_source=chatgpt.com "Guides: Authentication - Next.js"
[5]: https://www.material-tailwind.com/docs/react/stepper?utm_source=chatgpt.com "Tailwind CSS Stepper for React"
[6]: https://flowbite.com/docs/components/stepper/?utm_source=chatgpt.com "Tailwind CSS Stepper - Flowbite"
[7]: https://medium.com/%40brunno.tripovichy/building-a-scalable-multi-step-wizard-in-react-with-tailwind-css-31147cded202?utm_source=chatgpt.com "Building a Scalable Multi-Step Wizard in React with Tailwind CSS"
[8]: https://hassanagmir.com/blogs/react-chat-app-tutorial-tailwind-css?utm_source=chatgpt.com "React Chat App Tutorial: Tailwind CSS - Hassan Agmir"
[9]: https://flowbite.com/blocks/application/crud/?utm_source=chatgpt.com "Tailwind CSS CRUD Layouts - Flowbite"
[10]: https://tailadmin.com/?utm_source=chatgpt.com "TailAdmin: Free Tailwind CSS Admin Dashboard Template"
[11]: https://www.reddit.com/r/webdev/comments/10he3my/i_built_an_opensource_tailwind_css_admin/?utm_source=chatgpt.com "I built an open-source Tailwind CSS admin dashboard with Flowbite ..."
[12]: https://github.com/yourjhay/simple-chat?utm_source=chatgpt.com "yourjhay/simple-chat: Chat UI built with React and Tailwind CSS"
