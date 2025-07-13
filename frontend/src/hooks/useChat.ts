'use client'

import { useReducer, useCallback } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ChatMessage, chatApi, UserProfile } from '@/lib/api'
import DOMPurify from 'dompurify'

interface ChatState {
  messages: ChatMessage[]
  isLoading: boolean
  sessionId?: string
  userProfile: UserProfile
}

type ChatAction = 
  | { type: 'ADD_MESSAGE'; message: ChatMessage }
  | { type: 'SET_LOADING'; loading: boolean }
  | { type: 'UPDATE_PROFILE'; profile: UserProfile }
  | { type: 'SET_SESSION'; sessionId: string }
  | { type: 'CLEAR_CHAT' }

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  switch (action.type) {
    case 'ADD_MESSAGE':
      return { ...state, messages: [...state.messages, action.message] }
    case 'SET_LOADING':
      return { ...state, isLoading: action.loading }
    case 'UPDATE_PROFILE':
      return { ...state, userProfile: { ...state.userProfile, ...action.profile } }
    case 'SET_SESSION':
      return { ...state, sessionId: action.sessionId }
    case 'CLEAR_CHAT':
      return { messages: [], isLoading: false, userProfile: {} }
    default:
      return state
  }
}

export function useChat() {
  const queryClient = useQueryClient()
  const [state, dispatch] = useReducer(chatReducer, {
    messages: [],
    isLoading: false,
    userProfile: {}
  })

  const QUERY_KEYS = {
    CHAT_HISTORY: ['chat', 'history'] as const,
    USER_PROFILE: ['user', 'profile'] as const,
  }

  const chatMutation = useMutation({
    mutationFn: ({ message, sessionId }: { message: string; sessionId?: string }) => 
      chatApi.sendMessage(message, sessionId),
    onSuccess: (data) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.CHAT_HISTORY })
    },
  })

  const sendMessage = useCallback(async (content: string) => {
    // Sanitize user input
    const sanitizedContent = DOMPurify.sanitize(content)
    
    const userMessage: ChatMessage = {
      role: 'user',
      content: sanitizedContent,
      timestamp: new Date(),
      id: Date.now().toString()
    }

    dispatch({ type: 'ADD_MESSAGE', message: userMessage })
    dispatch({ type: 'SET_LOADING', loading: true })

    try {
      const response = await chatMutation.mutateAsync({
        message: sanitizedContent,
        sessionId: state.sessionId
      })
      
      // Sanitize assistant response
      const assistantContent = DOMPurify.sanitize(
        response.data.message || response.data.response
      )
      
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: assistantContent,
        timestamp: new Date(),
        id: (Date.now() + 1).toString()
      }

      dispatch({ type: 'ADD_MESSAGE', message: assistantMessage })
      dispatch({ type: 'SET_LOADING', loading: false })
      
      if (response.data.sessionId) {
        dispatch({ type: 'SET_SESSION', sessionId: response.data.sessionId })
      }
      
      if (response.data.userProfile) {
        dispatch({ type: 'UPDATE_PROFILE', profile: response.data.userProfile })
      }

      // 후속 질문이 있다면 추가 (sanitized)
      if (response.data.followUpQuestion) {
        const followUpMessage: ChatMessage = {
          role: 'assistant',
          content: DOMPurify.sanitize(response.data.followUpQuestion),
          timestamp: new Date(),
          id: (Date.now() + 2).toString()
        }

        dispatch({ type: 'ADD_MESSAGE', message: followUpMessage })
      }

    } catch (error) {
      console.error('Chat error:', error)
      
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: '죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해주세요.',
        timestamp: new Date(),
        id: (Date.now() + 1).toString()
      }

      dispatch({ type: 'ADD_MESSAGE', message: errorMessage })
      dispatch({ type: 'SET_LOADING', loading: false })
    }
  }, [state.sessionId, chatMutation])

  const clearChat = useCallback(() => {
    dispatch({ type: 'CLEAR_CHAT' })
  }, [])

  return {
    messages: state.messages,
    isLoading: state.isLoading,
    userProfile: state.userProfile,
    sendMessage,
    clearChat
  }
}