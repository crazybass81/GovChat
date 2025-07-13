'use client';
import {useState, useRef, useEffect} from 'react';

interface Msg { role: 'user'|'bot'; text: string; }

export default function ChatPage() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const prompt = inputRef.current?.value.trim();
    if (!prompt || isLoading) return;
    
    setMessages(m => [...m, {role: 'user', text: prompt}]);
    setIsLoading(true);
    
    try {
      // API 호출 예시 (실제 API 연동 시 수정 필요)
      setTimeout(() => {
        setMessages(m => [...m, {role: 'bot', text: '안녕하세요! 어떤 정부지원사업을 찾고 계신가요?'}]);
        setIsLoading(false);
      }, 1000);
    } catch (error) {
      setIsLoading(false);
    }
    
    if (inputRef.current) inputRef.current.value = '';
  };

  useEffect(() => window.scrollTo(0, document.body.scrollHeight), [messages]);

  return (
    <section className="flex flex-col h-full max-h-screen">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m,i) => (
          <p key={i} className={`px-4 py-2 rounded-lg max-w-lg ${m.role==='user'
              ? 'ml-auto bg-primary text-white' : 'bg-gray-100'}`}>
            {m.text}
          </p>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="border-t flex gap-2 p-4 bg-white">
        <input ref={inputRef} className="flex-1 border rounded-md px-3 py-2"
               placeholder="궁금한 점을 입력하세요…" />
        <button disabled={isLoading} className="btn-primary">전송</button>
      </form>
    </section>
  );
}