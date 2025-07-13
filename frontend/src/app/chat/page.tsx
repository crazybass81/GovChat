import { auth } from '@/lib/auth';
import { redirect } from 'next/navigation';
import ClientChat from './_components/ClientChat';

// 인증 쿠키 캐싱 방지
export const revalidate = 0;

export default async function ChatPage() {
  const session = await auth();
  
  if (!session) {
    redirect('/auth/signin?callbackUrl=/chat');
  }
  
  return <ClientChat user={session as any} />;
}