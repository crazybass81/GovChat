'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Policy, policyApi } from '@/lib/api'
import dynamic from 'next/dynamic'
import { ArrowLeftIcon } from '@heroicons/react/24/outline'

const Monaco = dynamic(() => import('@monaco-editor/react'), { ssr: false })

export default function PolicyDetailPage() {
  const params = useParams<{ id: string }>()
  const id = params?.id || ''
  const router = useRouter()
  const [policy, setPolicy] = useState<Policy | null>(null)
  const [yaml, setYaml] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    policyApi.getById(id).then(({ data }) => {
      setPolicy(data)
      setYaml(JSON.stringify(data.conditions, null, 2))
    })
  }, [id])

  const handleSave = async () => {
    setSaving(true)
    await policyApi.update(id, { conditions: JSON.parse(yaml) })
    setSaving(false)
    router.refresh()
  }

  if (!policy)
    return (
      <div className="min-h-screen flex items-center justify-center">
        로딩 중...
      </div>
    )

  return (
    <div className="min-h-screen bg-background p-6 space-y-4">
      <button
        onClick={() => router.back()}
        className="flex items-center text-textMuted hover:text-text focus-visible:outline-2 focus-visible:outline-primary"
      >
        <ArrowLeftIcon className="h-4 w-4 mr-1" /> 목록으로
      </button>

      <h1 className="text-3xl font-bold">{policy.id}</h1>
      <p className="text-sm">
        상태 <b>{policy.status}</b> · 생성일 <b>{new Date(policy.createdAt).toLocaleDateString()}</b>
      </p>

      <div className="border rounded-medium overflow-hidden h-[60vh]">
        <Monaco
          language="yaml"
          value={yaml}
          onChange={(v) => setYaml(v ?? '')}
          options={{ minimap: { enabled: false } }}
        />
      </div>

      <div className="flex gap-3">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-4 py-2 bg-primary text-white rounded-medium disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-primary"
        >
          {saving ? '저장 중…' : '저장'}
        </button>
        <button
          onClick={() => policyApi.publish(id)}
          className="px-4 py-2 bg-secondary text-white rounded-medium focus-visible:outline-2 focus-visible:outline-secondary"
        >
          발행
        </button>
      </div>
    </div>
  )
}