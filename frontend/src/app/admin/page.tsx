export default function AdminHome() {
  const cards = [
    { label: '오늘 상담', value: 134, color: 'text-blue-600' },
    { label: '신규 사용자', value: 27, color: 'text-green-600' },
    { label: '정책 초안', value: 12, color: 'text-yellow-600' },
    { label: '발행 대기', value: 4, color: 'text-red-600' },
  ];

  return (
    <div className="space-y-8 p-8">
      <h1 className="text-2xl font-bold">관리자 대시보드</h1>
      
      <section className="grid grid-cols-2 gap-6 lg:grid-cols-4">
        {cards.map(c => (
          <div key={c.label} className="rounded-lg bg-white border p-6 shadow-sm">
            <p className="text-sm text-gray-600 mb-1">{c.label}</p>
            <p className={`text-2xl font-semibold ${c.color}`}>{c.value}</p>
          </div>
        ))}
      </section>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border p-6">
          <h2 className="text-lg font-semibold mb-4">최근 상담 내역</h2>
          <div className="space-y-3">
            {[
              { title: '청년 창업 지원 문의', time: '10분 전' },
              { title: '중소기업 지원금 신청', time: '25분 전' },
              { title: 'R&D 지원사업 안내', time: '1시간 전' },
            ].map((item, i) => (
              <div key={i} className="flex justify-between items-center py-2 border-b last:border-b-0">
                <span className="text-sm">{item.title}</span>
                <span className="text-xs text-gray-500">{item.time}</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="bg-white rounded-lg border p-6">
          <h2 className="text-lg font-semibold mb-4">시스템 상태</h2>
          <div className="space-y-3">
            {[
              { label: 'API 응답시간', value: '0.8s' },
              { label: '오류율', value: '0.1%' },
              { label: '서버 상태', value: '정상' },
            ].map((item, i) => (
              <div key={i} className="flex justify-between items-center">
                <span className="text-sm text-gray-600">{item.label}</span>
                <span className="text-sm font-medium text-green-600">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}