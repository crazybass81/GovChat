'use client';
import {useState} from 'react';
import Link from 'next/link';

export default function SearchPage() {
  const [data] = useState([
    {id: 1, title: '청년창업지원사업', summary: '만 39세 이하 청년 창업자를 위한 자금 지원'},
    {id: 2, title: '소상공인 경영안정자금', summary: '소상공인 운영자금 및 시설자금 지원'},
  ]);

  return (
    <div className="max-w-4xl mx-auto p-6 grid gap-6">
      {data.map((p:any)=>(
        <article key={p.id} className="bg-white p-4 rounded-lg shadow-sm hover:shadow-md">
          <h2 className="text-lg font-semibold">{p.title}</h2>
          <p className="text-sm text-gray-600 line-clamp-2">{p.summary}</p>
          <Link href={`/program/${p.id}`} className="text-primary text-sm font-medium mt-2 inline-block">
            지원 조건 보기 →
          </Link>
        </article>
      ))}
    </div>
  );
}