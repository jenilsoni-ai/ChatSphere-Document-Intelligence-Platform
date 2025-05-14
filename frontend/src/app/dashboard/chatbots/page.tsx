'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { PlusIcon, ChatBubbleLeftRightIcon, TrashIcon } from '@heroicons/react/24/outline';
import { chatbotsAPI } from '@/lib/api';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';

interface Chatbot {
  id: string;
  name: string;
  description: string;
  createdAt: string;
  settings?: {
    role?: string;
  };
}

export default function ChatbotsPage() {
  const router = useRouter();
  const [chatbots, setChatbots] = useState<Chatbot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const { toast } = useToast();

  // Debug function to check authentication and API connectivity
  const runDebugCheck = async () => {
    try {
      setDebugInfo("Running diagnostics...");
      
      // Check token
      const token = localStorage.getItem('auth_token');
      const oldToken = localStorage.getItem('authToken');
      
      let tokenInfo = `Auth token ('auth_token'): ${token ? "Present" : "Missing"}\n`;
      tokenInfo += `Old auth token ('authToken'): ${oldToken ? "Present" : "Missing"}\n`;
      
      // Check backend connectivity
      let backendInfo = "Checking backend connectivity...\n";
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8080'}/health`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          backendInfo += `Backend health check: OK (${response.status})\n`;
          const data = await response.json();
          backendInfo += `Backend response: ${JSON.stringify(data)}\n`;
        } else {
          backendInfo += `Backend health check: Failed (${response.status})\n`;
          const text = await response.text();
          backendInfo += `Error: ${text}\n`;
        }
      } catch (err) {
        backendInfo += `Backend connection error: ${err instanceof Error ? err.message : String(err)}\n`;
      }
      
      // Also try the test endpoint that doesn't require authentication
      backendInfo += "\nTesting API endpoint without authentication...\n";
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8080'}/api/test`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        
        if (response.ok) {
          backendInfo += `API test endpoint: OK (${response.status})\n`;
          const data = await response.json();
          backendInfo += `API test response: ${JSON.stringify(data)}\n`;
        } else {
          backendInfo += `API test endpoint: Failed (${response.status})\n`;
          const text = await response.text();
          backendInfo += `Error: ${text}\n`;
        }
      } catch (err) {
        backendInfo += `API test connection error: ${err instanceof Error ? err.message : String(err)}\n`;
      }
      
      // Try to fetch chatbots with detailed logging
      let chatbotInfo = "Attempting to fetch chatbots...\n";
      try {
        const headers: Record<string, string> = {
          'Content-Type': 'application/json'
        };
        
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8080'}/api/chatbots`, {
          method: 'GET',
          headers
        });
        
        chatbotInfo += `Fetch status: ${response.status} ${response.statusText}\n`;
        
        if (response.ok) {
          const data = await response.json();
          chatbotInfo += `Received ${data.length} chatbots\n`;
        } else {
          const text = await response.text();
          chatbotInfo += `Error response: ${text}\n`;
        }
      } catch (err) {
        chatbotInfo += `Fetch error: ${err instanceof Error ? err.message : String(err)}\n`;
      }
      
      // Combine all debug info
      setDebugInfo(`=== DEBUG INFORMATION ===\n\n${tokenInfo}\n${backendInfo}\n${chatbotInfo}`);
    } catch (err) {
      setDebugInfo(`Debug error: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const fetchChatbots = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await chatbotsAPI.list();
      setChatbots(data);
    } catch (err) {
      console.error('Error fetching chatbots:', err);
      setError('Failed to load chatbots');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChatbots();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      // Optimistically update UI
      setChatbots(prevChatbots => prevChatbots.filter(bot => bot.id !== id));
      
      // Perform deletion
      await chatbotsAPI.delete(id);
      
      toast({
        title: "Chatbot deleted",
        description: "The chatbot has been successfully deleted",
      });
      setDeleteConfirmId(null);
      
      // Fetch latest data to ensure consistency
      await fetchChatbots();
    } catch (err) {
      console.error('Delete error:', err);
      
      // Revert optimistic update on error
      await fetchChatbots();
      
      toast({
        title: "Delete failed",
        description: err instanceof Error ? err.message : "Failed to delete the chatbot. Please try again.",
        variant: "destructive"
      });
    }
  };

  // Function to get the role from the chatbot settings, or default to "chatbot"
  const getChatbotType = (chatbot: Chatbot): string => {
    return chatbot.settings?.role || 'chatbot';
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Your Chatbots</h1>
        <div className="flex gap-2">
          <button
            onClick={runDebugCheck}
            className="px-4 py-2 bg-yellow-500 text-white rounded-md hover:bg-yellow-600"
          >
            Debug
          </button>
          <Link
            href="/dashboard/chatbots/new"
            className="inline-flex items-center px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
          >
            <PlusIcon className="w-5 h-5 mr-2" />
            Create New Chatbot
          </Link>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading your chatbots...</p>
        </div>
      ) : error ? (
        <div className="text-center py-12">
          <p className="text-red-500">{error}</p>
          <Button onClick={fetchChatbots} className="mt-4">
            Retry
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {chatbots.map((chatbot) => (
            <div key={chatbot.id} className="bg-card text-card-foreground rounded-lg border shadow-sm">
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold">{chatbot.name}</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      {chatbot.description || 'No description'}
                    </p>
                  </div>
                  <Dialog open={deleteConfirmId === chatbot.id} onOpenChange={(open) => !open && setDeleteConfirmId(null)}>
                    <DialogTrigger asChild>
                      <Button 
                        variant="ghost" 
                        size="icon"
                        onClick={() => setDeleteConfirmId(chatbot.id)}
                      >
                        <TrashIcon className="h-5 w-5 text-destructive" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Delete Chatbot</DialogTitle>
                        <DialogDescription>
                          Are you sure you want to delete "{chatbot.name}"? This action cannot be undone.
                          All chat sessions associated with this chatbot will be deleted.
                        </DialogDescription>
                      </DialogHeader>
                      <DialogFooter>
                        <Button 
                          variant="outline" 
                          onClick={() => setDeleteConfirmId(null)}
                        >
                          Cancel
                        </Button>
                        <Button 
                          variant="destructive"
                          onClick={() => handleDelete(chatbot.id)}
                        >
                          Delete
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </div>
                <div className="flex items-center text-sm text-muted-foreground">
                  <ChatBubbleLeftRightIcon className="w-4 h-4 mr-2" />
                  <span>{getChatbotType(chatbot)}</span>
                </div>
                <div className="mt-4 flex justify-end">
                  <Link
                    href={`/dashboard/chatbots/${chatbot.id}/config`}
                    className="text-sm text-primary hover:underline"
                  >
                    Configure →
                  </Link>
                </div>
              </div>
            </div>
          ))}

          {chatbots.length === 0 && (
            <div className="col-span-full text-center py-12">
              <ChatBubbleLeftRightIcon className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">No chatbots yet</h3>
              <p className="text-muted-foreground mb-4">
                Create your first chatbot to start building your AI assistant
              </p>
              <Link
                href="/dashboard/chatbots/new"
                className="inline-flex items-center px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
              >
                <PlusIcon className="w-5 h-5 mr-2" />
                Create Your First Chatbot
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
} 