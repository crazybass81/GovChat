import Link from 'next/link'
import { ChatBubbleLeftRightIcon, UserGroupIcon } from '@heroicons/react/24/outline'

// 정적 콘텐츠 - 1시간 캐싱
export const revalidate = 3600;

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
            <Link
              href="/chat"
              className="rounded-md bg-primary px-6 py-3 text-white shadow hover:bg-blue-700">
              Start Chat
            </Link>
            <Link
              href="/privacy"
              className="rounded-md px-6 py-3 text-gray-900 ring-1 ring-gray-300 hover:bg-gray-50">
              Learn more
            </Link>
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