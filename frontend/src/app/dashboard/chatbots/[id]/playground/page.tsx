'use client';

import React, { useState, useEffect } from 'react';
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { createChatSession, createChatMessage, getChatMessages, updateChatSession } from '@/lib/db';
import { ChatMessage, ChatSession } from '@/lib/types';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function PlaygroundPage({ params }: { params: { id: string } }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [role, setRole] = useState('assistant');
  const [instructions, setInstructions] = useState('');
  const [temperature, setTemperature] = useState([0.7]);
  const [primaryColor, setPrimaryColor] = useState('#007AFF');
  const [position, setPosition] = useState('bottom-right');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initializeChat = async () => {
      try {
        // Create a new chat session
        const session = await createChatSession({
          chatbot_id: params.id,
          visitor_id: null, // For playground, we don't track visitors
          platform: 'playground',
          device_info: {
            userAgent: navigator.userAgent,
            screenSize: {
              width: window.innerWidth,
              height: window.innerHeight
            }
          }
        });

        setSessionId(session.id);

        // Load existing messages if any
        const existingMessages = await getChatMessages(params.id, session.id);
        setMessages(existingMessages.map(msg => ({
          role: msg.role as 'user' | 'assistant',
          content: msg.content
        })));
      } catch (err) {
        setError('Failed to initialize chat session');
        console.error('Chat initialization error:', err);
      }
    };

    initializeChat();
  }, [params.id]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !sessionId) return;

    const newMessage: Message = {
      role: 'user',
      content: inputMessage
    };

    try {
      setMessages(prev => [...prev, newMessage]);
      setInputMessage('');
      setIsLoading(true);
      setError(null);

      // Save user message to database
      await createChatMessage({
        chatbot_id: params.id,
        session_id: sessionId,
        role: 'user',
        content: inputMessage,
        metadata: {
          temperature: temperature[0],
          instructions: instructions
        }
      });

      // Get AI response from the chat API
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          chatbotId: params.id,
          sessionId: sessionId,
          message: inputMessage,
          temperature: temperature[0],
          instructions: instructions
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to get response from chatbot');
      }

      const aiResponse = await response.json();
      setMessages(prev => [...prev, aiResponse]);
      setIsLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      console.error('Message sending error:', err);
      setIsLoading(false);
    }
  };

  // Update session when it ends
  useEffect(() => {
    const handleEndSession = async () => {
      if (sessionId) {
        try {
          await updateChatSession(sessionId, {
            end_time: new Date().toISOString(),
            message_count: messages.length
          });
        } catch (err) {
          console.error('Failed to update session:', err);
        }
      }
    };

    window.addEventListener('beforeunload', handleEndSession);
    return () => {
      window.removeEventListener('beforeunload', handleEndSession);
      handleEndSession();
    };
  }, [sessionId, messages.length]);

  const positions = [
    { value: 'bottom-right', label: 'Bottom Right' },
    { value: 'bottom-left', label: 'Bottom Left' },
    { value: 'top-right', label: 'Top Right' },
    { value: 'top-left', label: 'Top Left' },
  ];

  const roles = [
    { value: 'assistant', label: 'General Assistant' },
    { value: 'tutor', label: 'Educational Tutor' },
    { value: 'guide', label: 'Product Guide' },
    { value: 'expert', label: 'Domain Expert' },
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Chatbot Playground</h1>
      
      {error && (
        <div className="mb-4 p-4 bg-red-500/10 border border-red-500 rounded-md text-red-500">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Chat Interface Preview */}
        <div className="border rounded-lg p-4 bg-background" style={{ height: '600px' }}>
          <div className="flex flex-col h-full">
            <div className="flex-1 overflow-y-auto mb-4 space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-2 ${
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground ml-4'
                        : 'bg-muted mr-4'
                    }`}
                    style={{
                      backgroundColor: message.role === 'user' ? primaryColor : undefined
                    }}
                  >
                    {message.content}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="bg-muted rounded-lg px-4 py-2 mr-4">
                    <div className="flex space-x-2">
                      <div className="w-2 h-2 bg-foreground/50 rounded-full animate-bounce" />
                      <div className="w-2 h-2 bg-foreground/50 rounded-full animate-bounce [animation-delay:0.2s]" />
                      <div className="w-2 h-2 bg-foreground/50 rounded-full animate-bounce [animation-delay:0.4s]" />
                    </div>
                  </div>
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <Input
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                placeholder="Type your message..."
                className="flex-1"
              />
              <Button onClick={handleSendMessage} disabled={isLoading}>
                Send
              </Button>
            </div>
          </div>
        </div>

        {/* Customization Options */}
        <div className="space-y-6">
          <div>
            <Label>Role</Label>
            <Select value={role} onValueChange={setRole}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {roles.map((r) => (
                  <SelectItem key={r.value} value={r.value}>
                    {r.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Instructions</Label>
            <Textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="Enter specific instructions for your chatbot..."
              className="h-32"
            />
          </div>

          <div>
            <Label>Temperature (Creativity): {temperature[0]}</Label>
            <Slider
              value={temperature}
              onValueChange={setTemperature}
              min={0}
              max={1}
              step={0.1}
              className="my-4"
            />
            <p className="text-sm text-muted-foreground">
              Lower values make responses more focused and deterministic, higher values make them more creative and varied.
            </p>
          </div>

          <div>
            <Label>Primary Color</Label>
            <div className="flex gap-4 items-center">
              <Input
                type="color"
                value={primaryColor}
                onChange={(e) => setPrimaryColor(e.target.value)}
                className="w-20 h-10"
              />
              <Input
                type="text"
                value={primaryColor}
                onChange={(e) => setPrimaryColor(e.target.value)}
                className="flex-1"
              />
            </div>
          </div>

          <div>
            <Label>Widget Position</Label>
            <Select value={position} onValueChange={setPosition}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {positions.map((p) => (
                  <SelectItem key={p.value} value={p.value}>
                    {p.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button className="w-full">
            Save Changes
          </Button>

          <div className="mt-6 p-4 bg-muted rounded-lg">
            <h3 className="font-medium mb-2">Embed Code</h3>
            <code className="block p-4 bg-background rounded border text-sm overflow-x-auto">
              {`<script src="${window.location.origin}/widget/${params.id}.js"></script>`}
            </code>
            <Button variant="outline" className="mt-2 w-full" onClick={() => {
              navigator.clipboard.writeText(`<script src="${window.location.origin}/widget/${params.id}.js"></script>`);
            }}>
              Copy Code
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
} 