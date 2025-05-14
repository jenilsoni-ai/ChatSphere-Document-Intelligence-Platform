import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { name, description, knowledgeBase, type } = body;

    // Validate required fields
    if (!name || !description || !knowledgeBase || !type) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // TODO: Replace with your database logic
    const chatbot = {
      id: Date.now().toString(), // Replace with proper UUID in production
      name,
      description,
      knowledgeBase,
      type,
      createdAt: new Date().toISOString(),
    };

    // TODO: Save to your database
    
    return NextResponse.json(chatbot, { status: 201 });
  } catch (error) {
    console.error('Error creating chatbot:', error);
    return NextResponse.json(
      { error: 'Failed to create chatbot' },
      { status: 500 }
    );
  }
} 