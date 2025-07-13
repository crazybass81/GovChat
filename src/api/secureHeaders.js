export const secureHeaders = {
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'nonce-123456'; style-src 'self' 'nonce-123456';",
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Referrer-Policy': 'no-referrer',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
};