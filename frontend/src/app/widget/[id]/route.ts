import { NextRequest, NextResponse } from 'next/server';

/**
 * This route proxies requests for specific chatbot widget scripts to the backend
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    // Extract chatbot ID from params
    const chatbotId = params.id.replace(/\.js$/, ''); // Remove .js if present
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'; // Changed port to 8000
    const widgetUrl = `${backendUrl}/widget/${chatbotId}.js`;
    
    console.log(`Proxying widget request to: ${widgetUrl}`);
    
    const response = await fetch(widgetUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/javascript',
      },
    });

    if (!response.ok) {
      console.error(`Backend returned ${response.status}: ${response.statusText}`);
      return new NextResponse(`Widget not found: ${response.statusText}`, {
        status: response.status,
        headers: {
          'Content-Type': 'application/javascript',
        },
      });
    }

    const widgetJs = await response.text();
    
    return new NextResponse(widgetJs, {
      status: 200,
      headers: {
        'Content-Type': 'application/javascript',
        'Cache-Control': 'no-store, max-age=0',
        'Access-Control-Allow-Origin': '*',
      },
    });
  } catch (error) {
    console.error('Error proxying widget request:', error);
    return new NextResponse(`Error loading widget: ${error instanceof Error ? error.message : 'Unknown error'}`, {
      status: 500,
      headers: {
        'Content-Type': 'application/javascript',
      },
    });
  }
} 