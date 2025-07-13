'use client';
import {useState} from 'react';

export default function Policies() {
  const [data] = useState([
    {id: '1', title: '청년창업지원사업', status: 'DRAFT'},
    {id: '2', title: '소상공인 경영안정자금', status: 'PUBLISHED'},
  ]);

  const publish = (id: string) => {
    console.log('Publishing policy:', id);
  };

  return (
    <div className="p-8">
      <h1 className="text-xl font-bold mb-4">정책 목록</h1>
      <table className="w-full text-sm">
        <thead><tr className="text-left">
          <th>제목</th><th>상태</th><th className="w-40">작업</th>
        </tr></thead>
        <tbody>
          {data.map((p:any)=>(
            <tr key={p.id} className="border-t">
              <td>{p.title}</td><td>{p.status}</td>
              <td className="space-x-2 py-1">
                <button className="btn-primary" onClick={()=>publish(p.id)}>발행</button>
                <button className="btn" onClick={()=>{/* edit nav */}}>수정</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}