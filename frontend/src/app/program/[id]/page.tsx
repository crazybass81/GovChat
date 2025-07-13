export const revalidate = 3600;

export default async function ProgramDetailPage({ params }: { params: { id: string } }) {
  // Mock data fetch
  const data = {
    title: 'AI 바우처 지원사업',
    tags: ['스타트업', 'AI', '청년'],
    desc: 'AI 바우처 지원 사업으로 인공지능 기술을 활용한 스타트업을 지원합니다.',
    amount: '최대 5천만원',
    period: '2024.01.01 ~ 2024.12.31',
    eligibility: ['만 39세 이하', '예비창업자 또는 창업 3년 이내', 'AI 관련 사업'],
    applyUrl: 'https://apply.gov.kr'
  };

  return (
    <div className="mx-auto max-w-3xl p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-4">{data.title}</h1>
        <div className="flex gap-2 mb-6">
          {data.tags.map(t => (
            <span key={t} className="rounded bg-blue-50 px-3 py-1 text-xs text-blue-700">
              {t}
            </span>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-lg border p-6 space-y-4">
        <h2 className="text-xl font-semibold">사업 개요</h2>
        <p className="text-gray-600 leading-relaxed">{data.desc}</p>
        
        <div className="grid md:grid-cols-2 gap-6 pt-4">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">지원 금액</h3>
            <p className="text-gray-600">{data.amount}</p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">신청 기간</h3>
            <p className="text-gray-600">{data.period}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg border p-6">
        <h2 className="text-xl font-semibold mb-4">지원 자격</h2>
        <ul className="space-y-2">
          {data.eligibility.map((item, i) => (
            <li key={i} className="flex items-center gap-2">
              <div className="w-2 h-2 bg-primary rounded-full" />
              <span className="text-gray-600">{item}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="flex gap-4">
        <a 
          href={data.applyUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-1 bg-primary text-white text-center py-3 rounded-md hover:bg-blue-700 font-medium">
          신청 바로가기
        </a>
        <button className="px-6 py-3 border border-gray-300 rounded-md hover:bg-gray-50">
          문의하기
        </button>
      </div>
    </div>
  )
}