// src/config/config.ts

// Ensure NEXT_PUBLIC_ is prepended for browser-accessible environment variables in Next.js
export const NEXT_PUBLIC_BACKEND_API_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';

// Log the backend URL being used during build or server startup (won't show in browser console)
console.log(`Using backend API URL: ${NEXT_PUBLIC_BACKEND_API_URL}`);

