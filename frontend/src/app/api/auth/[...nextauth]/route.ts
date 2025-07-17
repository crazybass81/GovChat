import NextAuth from 'next-auth';
import Google from 'next-auth/providers/google';
import Kakao from 'next-auth/providers/kakao';
import Naver from 'next-auth/providers/naver';
import Credentials from 'next-auth/providers/credentials';
import { DynamoDBAdapter } from '@auth/dynamodb-adapter';
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocument } from '@aws-sdk/lib-dynamodb';
import bcrypt from 'bcryptjs';
import { getOAuthConfig } from '@/lib/auth-config';

// DynamoDB 클라이언트 설정
const dynamoClient = DynamoDBDocument.from(new DynamoDBClient({
  region: process.env.AWS_REGION || 'ap-northeast-2',
  ...(process.env.NODE_ENV === 'development' && {
    endpoint: process.env.DYNAMODB_ENDPOINT,
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID || 'dummy',
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || 'dummy',
    },
  }),
}));

// 통합 사용자 검증 함수
async function verifyCredentials(email: string, password: string) {
  try {
    // UserTable에서 사용자 조회
    const result = await dynamoClient.get({
      TableName: 'UserTable',
      Key: { email }
    });
    
    const user = result.Item;
    
    // 사용자가 존재하지 않거나 비밀번호가 없는 경우
    if (!user || !user.password_hash) {
      // 기본 마스터 계정 지원 (환경변수 사용)
      const defaultAdminEmail = process.env.DEFAULT_ADMIN_EMAIL || 'admin@govchat.ai';
      const defaultAdminPassword = process.env.DEFAULT_ADMIN_PASSWORD || 'admin123';
      
      if (email === defaultAdminEmail && password === defaultAdminPassword) {
        return {
          id: email,
          email: email,
          name: 'Master Admin',
          role: 'master'
        };
      }
      return null;
    }
    
    // 비밀번호 검증
    const isValid = await bcrypt.compare(password, user.password_hash);
    if (!isValid) return null;
    
    // 계정 활성화 확인
    if (!user.active) return null;
    
    // 인증 성공
    return {
      id: email,
      email: email,
      name: user.name || email.split('@')[0],
      role: user.user_type || 'user' // user_type 필드 사용
    };
  } catch (error) {
    console.error('Credential verification error:', error);
    
    // 기본 마스터 계정 지원 (환경변수 사용)
    const defaultAdminEmail = process.env.DEFAULT_ADMIN_EMAIL || 'admin@govchat.ai';
    const defaultAdminPassword = process.env.DEFAULT_ADMIN_PASSWORD || 'admin123';
    
    if (email === defaultAdminEmail && password === defaultAdminPassword) {
      return {
        id: email,
        email: email,
        name: 'Master Admin',
        role: 'master'
      };
    }
    
    return null;
  }
}

// OAuth 설정을 비동기로 가져오기
let oauthConfig: any = null;

async function getProviders() {
  if (!oauthConfig) {
    oauthConfig = await getOAuthConfig();
  }
  
  return [
    // Google OAuth (환경변수 사용)
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    // Kakao OAuth (SSM Parameter 사용)
    Kakao({
      clientId: oauthConfig.kakao.clientId,
      clientSecret: oauthConfig.kakao.clientSecret,
    }),
    // Naver OAuth (환경변수 사용)
    Naver({
      clientId: process.env.NAVER_CLIENT_ID!,
      clientSecret: process.env.NAVER_CLIENT_SECRET!,
    }),
    // 이메일/비밀번호 인증
    Credentials({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      authorize: async (credentials) => {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }
        
        const user = await verifyCredentials(
          credentials.email as string,
          credentials.password as string
        );
        
        return user;
      },
    }),
  ];
}

const authConfig = {
  adapter: DynamoDBAdapter(dynamoClient, {
    tableName: process.env.AUTH_DYNAMODB_TABLE || 'govchat-auth',
  }),
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    Kakao({
      clientId: process.env.KAKAO_CLIENT_ID!,
      clientSecret: process.env.KAKAO_CLIENT_SECRET!,
    }),
    Naver({
      clientId: process.env.NAVER_CLIENT_ID!,
      clientSecret: process.env.NAVER_CLIENT_SECRET!,
    }),
    Credentials({
      name: 'credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      authorize: async (credentials) => {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }
        
        const user = await verifyCredentials(
          credentials.email as string,
          credentials.password as string
        );
        
        return user;
      },
    }),
  ],
  session: { 
    strategy: 'jwt' as const, 
    maxAge: 30 * 24 * 60 * 60, // 30일
  },
  secret: process.env.NEXTAUTH_SECRET!,
  callbacks: {
    async jwt(params: any) {
      const { token, account, user } = params;
      if (account) {
        token.provider = account.provider;
      }
      if (user) {
        token.userId = user.id;
        // 관리자 역할 정보 추가
        if (user.role) {
          token.role = user.role;
        }
      }
      return token;
    },
    async session(params: any) {
      const { session, token } = params;
      if (token) {
        session.user.id = token.userId as string;
        session.provider = token.provider as string;
        // 관리자 역할 정보 추가
        if (token.role) {
          session.user.role = token.role as string;
        }
      }
      return session;
    },
  },
  pages: {
    signIn: '/auth/signin',
    error: '/auth/error',
  },
  debug: process.env.NODE_ENV === 'development',
};

const handler = NextAuth(authConfig);

export { handler as GET, handler as POST };