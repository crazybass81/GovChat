'use client';
import { useState, useRef, useEffect } from 'react';
import { PaperAirplaneIcon } from '@heroicons/react/24/solid';

interface Message {
  role: 'user' | 'bot';
  text: string;
}

export default function ClientChat({ user }: { user: any }) {
  const [msgs, setMsgs] = useState<Message[]>([]);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), [msgs]);

  async function send(prompt: string) {
    setMsgs(m => [...m, { role: 'user', text: prompt }, { role: 'bot', text: '…' }]);
    
    // Mock streaming
    await new Promise(r => setTimeout(r, 600));
    setMsgs(m => m.map((msg, i) => 
      i === m.length - 1 ? { role: 'bot', text: '답변입니다. 어떤 지원사업을 찾고 계신가요?' } : msg
    ));
  }

  return (
    <section className="flex h-screen max-h-screen flex-col">
      <div className="flex-1 overflow-y-auto p-4">
        {msgs.length === 0 && (
          <div className="text-center text-gray-500 mt-20">
            <p>안녕하세요! 정부지원사업 상담을 시작해보세요.</p>
          </div>
        )}
        
        {msgs.map((m, i) => (
          <div key={i} className={`mb-4 flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-lg rounded-lg px-4 py-2 ${
              m.role === 'user' 
                ? 'bg-primary text-white' 
                : 'bg-gray-100 text-gray-900'
            }`}>
              {m.text}
            </div>
          </div>
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
        <textarea 
          ref={inputRef} 
          rows={1} 
          className="flex-1 resize-none rounded-md border p-2" 
          placeholder="메시지를 입력…" 
        />
        <button className="px-4 py-2 bg-primary text-white rounded-md hover:bg-blue-700">
          <PaperAirplaneIcon className="h-5 w-5" />
        </button>
      </form>
    </section>
  );
}