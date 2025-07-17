'use client';

import React, { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';

interface AdminUser {
  email: string;
  role: 'master' | 'admin';
  name?: string;
  invited?: boolean;
  created_at?: string;
}

export default function AdminsPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [admins, setAdmins] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [newAdminEmail, setNewAdminEmail] = useState('');
  const [isInviting, setIsInviting] = useState(false);

  useEffect(() => {
    // 마스터 관리자만 접근 가능
    if (status === 'authenticated') {
      if (session?.user?.role !== 'master') {
        router.push('/admin');
        return;
      }
      fetchAdmins();
    } else if (status === 'unauthenticated') {
      router.push('/admin/login');
    }
  }, [status, session, router]);

  const fetchAdmins = async () => {
    try {
      const response = await fetch('/api/admin/admins');
      if (response.ok) {
        const data = await response.json();
        setAdmins(data.admins || []);
      } else {
        console.error('관리자 목록 로드 실패');
      }
    } catch (error) {
      console.error('관리자 목록 로드 오류:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAdminEmail.trim()) return;

    setIsInviting(true);
    try {
      const response = await fetch('/api/admin/admins', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: newAdminEmail })
      });

      if (response.ok) {
        alert('관리자 초대가 발송되었습니다.');
        setNewAdminEmail('');
        fetchAdmins();
      } else {
        const data = await response.json();
        alert(`초대 실패: ${data.error || '알 수 없는 오류'}`);
      }
    } catch (error) {
      alert('관리자 초대 중 오류가 발생했습니다.');
    } finally {
      setIsInviting(false);
    }
  };

  const handleDelete = async (email: string) => {
    if (!confirm(`정말 ${email} 관리자를 삭제하시겠습니까?`)) return;

    try {
      const response = await fetch('/api/admin/admins', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      if (response.ok) {
        alert('관리자가 삭제되었습니다.');
        fetchAdmins();
      } else {
        const data = await response.json();
        alert(`삭제 실패: ${data.error || '알 수 없는 오류'}`);
      }
    } catch (error) {
      alert('관리자 삭제 중 오류가 발생했습니다.');
    }
  };

  if (status === 'loading' || (status === 'authenticated' && loading)) {
    return <div className="p-6">로딩 중...</div>;
  }

  return (
    <div>
      <h2 className="text-xl font-bold mb-6">관리자 관리</h2>

      {/* 관리자 초대 폼 */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h3 className="text-lg font-semibold mb-4">새 관리자 초대</h3>
        <form onSubmit={handleInvite} className="flex gap-2">
          <input
            type="email"
            value={newAdminEmail}
            onChange={(e) => setNewAdminEmail(e.target.value)}
            placeholder="관리자 이메일"
            className="flex-1 p-2 border rounded"
            required
          />
          <Button
            type="submit"
            disabled={isInviting}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {isInviting ? '초대 중...' : '초대'}
          </Button>
        </form>
      </div>

      {/* 관리자 목록 */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-4 font-medium">이메일</th>
              <th className="text-left p-4 font-medium">역할</th>
              <th className="text-left p-4 font-medium">상태</th>
              <th className="p-4 font-medium">액션</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {admins.length === 0 ? (
              <tr>
                <td colSpan={4} className="text-center py-8 text-gray-500">
                  등록된 관리자가 없습니다.
                </td>
              </tr>
            ) : (
              admins.map((admin) => (
                <tr key={admin.email} className="hover:bg-gray-50">
                  <td className="p-4">{admin.email}</td>
                  <td className="p-4">
                    {admin.role === 'master' ? '마스터' : '관리자'}
                  </td>
                  <td className="p-4">
                    <span
                      className={`px-2 py-1 rounded-full text-xs ${
                        admin.invited
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-green-100 text-green-800'
                      }`}
                    >
                      {admin.invited ? '초대됨' : '활성'}
                    </span>
                  </td>
                  <td className="p-4">
                    {admin.role !== 'master' && (
                      <button
                        onClick={() => handleDelete(admin.email)}
                        className="text-red-600 hover:underline text-sm"
                      >
                        삭제
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}