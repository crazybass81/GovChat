const { createSecureHeaders } = require('next-secure-headers')

/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE || 'https://x94nllzgi0.execute-api.us-east-1.amazonaws.com/prod'
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: createSecureHeaders({
          contentSecurityPolicy: {
            directives: {
              defaultSrc: "'self'",
              styleSrc: ["'self'", "'unsafe-inline'", "fonts.googleapis.com"],
              fontSrc: ["'self'", "fonts.gstatic.com"],
              imgSrc: ["'self'", "data:", "https:"],
              scriptSrc: ["'self'", "'unsafe-eval'"],
              connectSrc: ["'self'", process.env.NEXT_PUBLIC_API_BASE || 'https://x94nllzgi0.execute-api.us-east-1.amazonaws.com'],
              frameSrc: "'none'",
              objectSrc: "'none'",
              baseUri: "'self'",
              formAction: "'self'",
              frameAncestors: "'none'",
            },
          },
          forceHTTPSRedirect: [true, { maxAge: 60 * 60 * 24 * 4, includeSubDomains: true }],
          referrerPolicy: "same-origin"
        })
      }
    ]
  }
}

module.exports = nextConfig