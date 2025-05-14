import { NextResponse } from 'next/server';
import { createChatMessage, getChatbot, getKnowledgeBase } from '@/lib/db';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { chatbotId, sessionId, message, temperature = 0.7, instructions = '' } = body;

    if (!chatbotId || !sessionId || !message) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // Get chatbot configuration
    const chatbot = await getChatbot(chatbotId);
    if (!chatbot) {
      return NextResponse.json(
        { error: 'Chatbot not found' },
        { status: 404 }
      );
    }

    // Get knowledge base
    const knowledgeBase = await getKnowledgeBase(chatbotId);
    if (!knowledgeBase) {
      return NextResponse.json(
        { error: 'Knowledge base not found' },
        { status: 404 }
      );
    }

    // TODO: Replace this with actual AI processing
    // For now, we'll return a mock response
    const response = {
      role: 'assistant',
      content: `This is a simulated response based on:
- Knowledge base content length: ${knowledgeBase.content.length} characters
- Temperature: ${temperature}
- Instructions: ${instructions || 'None'}
- Chatbot role: ${chatbot.role}

Your message was: "${message}"

In production, this would use the knowledge base content and AI to generate a relevant response.`
    };

    // Save the response to the database
    await createChatMessage({
      chatbot_id: chatbotId,
      session_id: sessionId,
      role: 'assistant',
      content: response.content,
      metadata: {
        temperature,
        instructions
      }
    });

    return NextResponse.json(response);
  } catch (error) {
    console.error('Chat API error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
} 