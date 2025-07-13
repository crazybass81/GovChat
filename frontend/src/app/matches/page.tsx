import Link from 'next/link'

export const revalidate = 60;

export default function MatchesPage() {
  const dummy = Array.from({ length: 8 }).map((_, i) => ({
    id: i,
    title: `지원사업 ${i + 1}`,
    summary: '사업 요약 설명입니다. 자세한 내용은 클릭해서 확인하세요.',
    matchRate: Math.floor(Math.random() * 30) + 70,
    tags: ['청년', '창업', 'AI'][Math.floor(Math.random() * 3)]
  }));

  return (
    <div className="mx-auto max-w-5xl gap-6 p-8">
      <h1 className="text-3xl font-bold mb-8">매칭된 지원사업</h1>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {dummy.map(p => (
          <article key={p.id} className="rounded-lg border bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start mb-3">
              <span className="inline-block rounded bg-blue-50 px-2 py-1 text-xs text-blue-700">
                {p.tags}
              </span>
              <span className="text-sm font-medium text-green-600">
                매칭률 {p.matchRate}%
              </span>
            </div>
            
            <h2 className="text-lg font-semibold mb-2">{p.title}</h2>
            <p className="text-sm text-gray-600 mb-4 line-clamp-2">{p.summary}</p>
            
            <Link 
              href={`/program/${p.id}`} 
              className="inline-block text-primary hover:underline font-medium">
              자세히 보기 →
            </Link>
          </article>
        ))}
      </div>
    </div>
  )
}