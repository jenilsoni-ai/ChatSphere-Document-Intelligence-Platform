import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  async headers() {
    return [
      {
        // Allow JavaScript files to be served from the widget route
        source: '/widget/:path*',
        headers: [
          {
            key: 'Content-Type',
            value: 'application/javascript',
          },
          {
            key: 'Access-Control-Allow-Origin',
            value: '*',
          },
          {
            key: 'Cache-Control',
            value: 'no-cache, no-store, must-revalidate',
          },
        ],
      },

      // Add this new headers configuration
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: '*',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, PUT, DELETE, OPTIONS',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization',
          },
        ],
      },

    ];
  },
  
  // Add rewrites to proxy API requests to the backend
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    return [
      // Widget request handling
      {
        // Handle widget script requests
        source: '/widget/:id',
        destination: `${backendUrl}/widget/:id.js`,
      },
      // API request handling
      {
        // Proxy widget API requests to the backend
        source: '/api/chat/widget/:path*',
        destination: `${backendUrl}/api/chat/widget/:path*`,
      },
      {
        // Proxy chatbot config requests for the widget
        source: '/api/chatbots/widget-config/:chatbotId',
        destination: `${backendUrl}/api/chatbots/widget-config/:chatbotId`,
      },
      {
        source: '/api/health',
        destination: `${backendUrl}/health`,
      },
      {
        source: '/api/vector-db',
        destination: `${backendUrl}/api/vector-db`,
      },
      // Proxy vector store settings API
      {
        source: '/api/settings/vector-store',
        destination: `${backendUrl}/api/settings/vector-store`,
      },
      {
        source: '/api/settings/vector-store/:path*',
        destination: `${backendUrl}/api/settings/vector-store/:path*`,
      },
    ];
  },
};

export default nextConfig;
