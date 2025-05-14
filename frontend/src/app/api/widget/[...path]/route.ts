import { NextRequest, NextResponse } from 'next/server';

/**
 * This route proxies requests to the widget.js file on the backend server
 */
export async function GET(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  try {
    const path = params.path.join('/');
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const widgetUrl = `${backendUrl}/widget/${path}`;
    
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