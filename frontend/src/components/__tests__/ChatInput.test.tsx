/**
 * @vitest-environment jsdom
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'

// Mock chat input component
const MockChatInput = ({ onSend }: { onSend: (message: string) => void }) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const formData = new FormData(e.target as HTMLFormElement)
    const message = formData.get('message') as string
    if (message.trim()) {
      onSend(message)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        name="message"
        type="text"
        placeholder="메시지를 입력하세요..."
        className="flex-1 p-2 border rounded"
      />
      <button type="submit" className="px-4 py-2 bg-blue-500 text-white rounded">
        전송
      </button>
    </form>
  )
}

describe('ChatInput', () => {
  it('renders input field and send button', () => {
    const mockOnSend = vi.fn()
    render(<MockChatInput onSend={mockOnSend} />)
    
    expect(screen.getByPlaceholderText('메시지를 입력하세요...')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '전송' })).toBeInTheDocument()
  })

  it('calls onSend when form is submitted with message', async () => {
    const mockOnSend = vi.fn()
    render(<MockChatInput onSend={mockOnSend} />)
    
    const input = screen.getByPlaceholderText('메시지를 입력하세요...')
    const button = screen.getByRole('button', { name: '전송' })
    
    fireEvent.change(input, { target: { value: '안녕하세요' } })
    fireEvent.click(button)
    
    await waitFor(() => {
      expect(mockOnSend).toHaveBeenCalledWith('안녕하세요')
    })
  })

  it('does not call onSend with empty message', async () => {
    const mockOnSend = vi.fn()
    render(<MockChatInput onSend={mockOnSend} />)
    
    const button = screen.getByRole('button', { name: '전송' })
    fireEvent.click(button)
    
    expect(mockOnSend).not.toHaveBeenCalled()
  })
})