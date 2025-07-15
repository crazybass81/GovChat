import { NextResponse } from 'next/server'
import { DynamoDBClient } from '@aws-sdk/client-dynamodb'
import { DynamoDBDocument } from '@aws-sdk/lib-dynamodb'

const dynamoClient = DynamoDBDocument.from(new DynamoDBClient({
  region: 'us-east-1',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
}))

export async function GET() {
  try {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const thisWeek = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
    const thisMonth = new Date(now.getFullYear(), now.getMonth(), 1)

    const response = await dynamoClient.scan({
      TableName: 'gov-support-sessions',
      ProjectionExpression: 'created_at, session_id'
    })

    const sessions = response.Items || []
    
    let todayCount = 0
    let weekCount = 0
    let monthCount = 0

    sessions.forEach(session => {
      if (session.created_at) {
        const createdAt = new Date(session.created_at)
        if (createdAt >= today) todayCount++
        if (createdAt >= thisWeek) weekCount++
        if (createdAt >= thisMonth) monthCount++
      }
    })

    return NextResponse.json({
      today: todayCount,
      thisWeek: weekCount,
      thisMonth: monthCount
    })
  } catch (error) {
    console.error('Recent matches API error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch recent matches' },
      { status: 500 }
    )
  }
}