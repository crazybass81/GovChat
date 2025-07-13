'use client'

import Image from 'next/image'

interface SocialButtonProps {
  provider: 'google' | 'naver' | 'kakao'
  onClick: () => void
}

const logo = {
  google: '/logos/google.svg',
  naver: '/logos/naver.svg',
  kakao: '/logos/kakao.svg',
}

export default function SocialButton({ provider, onClick }: SocialButtonProps) {
  return (
    <button
      onClick={onClick}
      className="flex items-center justify-center w-full border rounded-medium py-2 hover:bg-gray-50 focus-visible:outline-2 focus-visible:outline-primary"
    >
      <Image src={logo[provider]} alt={provider} width={20} height={20} />
      <span className="ml-2 capitalize">{provider}로 계속하기</span>
    </button>
  )
}