export const revalidate = 0;

export default function MyPage() {
  const complete = 60;
  
  return (
    <div className="mx-auto max-w-md p-12 space-y-6">
      <h1 className="text-xl font-bold">내 정보</h1>
      
      <div className="bg-white rounded-lg border p-6 space-y-4">
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium">프로필 완성도</span>
            <span className="text-sm text-gray-600">{complete}%</span>
          </div>
          <div className="h-2 w-full rounded bg-gray-200">
            <div 
              className="h-2 rounded bg-primary transition-all duration-300" 
              style={{ width: `${complete}%` }} 
            />
          </div>
        </div>
        
        <div className="pt-4 space-y-3">
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">이름</span>
            <span className="text-sm font-medium">홍길동</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">이메일</span>
            <span className="text-sm font-medium">user@example.com</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">지역</span>
            <span className="text-sm font-medium">서울특별시</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-gray-600">업종</span>
            <span className="text-sm text-gray-400">미입력</span>
          </div>
        </div>
      </div>
      
      <button className="w-full bg-primary text-white py-3 rounded-md hover:bg-blue-700 font-medium">
        정보 수정
      </button>
      
      <div className="space-y-2">
        <button className="w-full text-left py-2 text-gray-600 hover:text-gray-900">
          내 상담 내역
        </button>
        <button className="w-full text-left py-2 text-gray-600 hover:text-gray-900">
          알림 설정
        </button>
        <button className="w-full text-left py-2 text-red-600 hover:text-red-700">
          로그아웃
        </button>
      </div>
    </div>
  )
}