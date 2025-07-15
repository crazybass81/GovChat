import { NextRequest, NextResponse } from 'next/server'
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
    const [policiesResult, usersResult, sessionsResult] = await Promise.all([
      dynamoClient.scan({ 
        TableName: 'PoliciesTable',
        Select: 'COUNT'
      }),
      dynamoClient.scan({ 
        TableName: 'UserTable',
        Select: 'COUNT'
      }),
      dynamoClient.scan({ 
        TableName: 'gov-support-sessions',
        Select: 'COUNT'
      })
    ])

    const stats = {
      totalPolicies: policiesResult.Count || 0,
      totalUsers: usersResult.Count || 0,
      totalMatches: sessionsResult.Count || 0
    }

    return NextResponse.json(stats)
  } catch (error) {
    console.error('Stats API error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch stats' },
      { status: 500 }
    )
  }
}