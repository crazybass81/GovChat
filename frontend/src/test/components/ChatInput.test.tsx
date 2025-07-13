import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import ChatPage from '@/app/user/chat/page'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Mock useChat hook
vi.mock('@/hooks/useChat', () => ({
  useChat: () => ({
    messages: [],
    isLoading: false,
    userProfile: {},
    sendMessage: vi.fn(),
    clearChat: vi.fn()
  })
}))

describe('ChatInput', () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  })

  const renderWithProvider = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    )
  }

  it('renders chat input correctly', () => {
    renderWithProvider(<ChatPage />)
    
    expect(screen.getByPlaceholderText('메시지를 입력하세요...')).toBeInTheDocument()
    expect(screen.getByLabelText('메시지 전송')).toBeInTheDocument()
  })

  it('disables submit button when input is empty', () => {
    renderWithProvider(<ChatPage />)
    
    const submitButton = screen.getByLabelText('메시지 전송')
    expect(submitButton).toBeDisabled()
  })

  it('enables submit button when input has text', async () => {
    renderWithProvider(<ChatPage />)
    
    const input = screen.getByPlaceholderText('메시지를 입력하세요...')
    const submitButton = screen.getByLabelText('메시지 전송')
    
    fireEvent.change(input, { target: { value: '안녕하세요' } })
    
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled()
    })
  })
})