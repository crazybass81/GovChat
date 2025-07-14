'use client';

import React from 'react';

interface User {
    id: number;
    name: string;
    email: string;
    signedUp: string;
    lastLogin: string;
}

export default function UsersPage() {
    // 예시용 사용자 데이터 (실제로는 API를 통해 불러옴)
    const users: User[] = [
        { id: 1, name: '홍길동', email: 'hong@example.com', signedUp: '2025-06-01', lastLogin: '2025-07-12' },
        { id: 2, name: '김지원', email: 'kim@example.com', signedUp: '2025-06-15', lastLogin: '2025-07-13' },
        // ... (기타 사용자들)
    ];

    return (
        <div>
            <h2 className="text-xl font-bold mb-4">사용자 목록</h2>
            <table className="min-w-full border-t border-b text-sm">
                <thead className="bg-gray-100">
                    <tr>
                        <th className="text-left p-2">이름</th>
                        <th className="text-left p-2">이메일</th>
                        <th className="text-left p-2">가입일</th>
                        <th className="text-left p-2">마지막 접속일</th>
                    </tr>
                </thead>
                <tbody>
                    {users.map(user => (
                        <tr key={user.id} className="border-b hover:bg-gray-50">
                            <td className="p-2">{user.name}</td>
                            <td className="p-2">{user.email}</td>
                            <td className="p-2">{user.signedUp}</td>
                            <td className="p-2">{user.lastLogin}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
