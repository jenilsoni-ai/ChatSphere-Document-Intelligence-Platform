'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { InfoIcon, RefreshCw, Save, Zap, Monitor, Smartphone, SendIcon, Code, Copy, Check } from 'lucide-react';
import { Chatbot } from '@/lib/types';
import { useRouter } from 'next/navigation';

export default function ChatbotConfigPage({ params }: { params: { id: string } }) {
  // Unwrap the params object using React.use()
  const unwrappedParams = React.use(params as any);
  const chatbotId = unwrappedParams.id;
  
  // Basic configuration
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [role, setRole] = useState('assistant');
  const [instructions, setInstructions] = useState('');
  const [documents, setDocuments] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Advanced configuration
  const [temperature, setTemperature] = useState([0.7]);
  const [maxTokens, setMaxTokens] = useState([2048]);
  const [initialMessage, setInitialMessage] = useState('');
  const [enableMemory, setEnableMemory] = useState(true);
  const [memoryWindow, setMemoryWindow] = useState([10]);
  
  // Appearance configuration
  const [primaryColor, setPrimaryColor] = useState('#007AFF');
  const [secondaryColor, setSecondaryColor] = useState('#F2F2F7');
  const [position, setPosition] = useState('bottom-right');
  const [chatTitle, setChatTitle] = useState('Chat with our AI');
  const [showBranding, setShowBranding] = useState(true);
  
  // Preview state
  const [messages, setMessages] = useState<{
    role: 'user' | 'assistant'; 
    content: string;
    sources?: Array<{
      document_id: string;
      chunkId: string;
      score: number;
    }>;
  }[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [activeTab, setActiveTab] = useState('basic');
  const [previewMode, setPreviewMode] = useState('desktop');
  const [isSaving, setIsSaving] = useState(false);
  const [isChanged, setIsChanged] = useState(false);
  const [isCopied, setIsCopied] = useState(false);
  
  // Chat container ref for scrolling
  const chatContainerRef = useRef<HTMLDivElement>(null);
  
  // Example system prompts for different roles
  const rolePrompts = {
    assistant: 'You are a helpful assistant for our company. Be concise, friendly, and provide accurate information based on what you know.',
    tutor: 'You are an educational tutor. Explain concepts clearly, provide examples, and guide the user through learning new topics step by step.',
    guide: 'You are a product guide for our platform. Help users understand features, provide usage tips, and troubleshoot common issues.',
    expert: 'You are a domain expert. Provide in-depth, technical answers and insights based on the latest knowledge in the field.'
  };

  const router = useRouter();

  // Fetch chatbot data when component mounts
  useEffect(() => {
    const fetchChatbotData = async () => {
      try {
        setIsLoading(true);
        const token = localStorage.getItem('auth_token');
        if (!token) {
          console.error('No auth token found');
          return;
        }

        console.log(`Fetching chatbot data for ID: ${chatbotId}`);
        const response = await fetch(`http://localhost:8000/api/chatbots/${chatbotId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          console.error('Failed to fetch chatbot:', response.status);
          const errorText = await response.text();
          console.error('Error response:', errorText);
          throw new Error(`Failed to fetch chatbot: ${response.status}`);
        }

        const data = await response.json();
        setName(data.name || '');
        setDescription(data.description || '');
        setDocuments(data.documents || []);
        
        // Set settings
        if (data.settings) {
          setTemperature([data.settings.temperature || 0.7]);
          setMaxTokens([data.settings.maxTokens || 2048]);
          setInstructions(data.settings.instructions || '');
          
          // Set role if available
          if (data.settings.role) {
            setRole(getRoleValue(data.settings.role) || 'assistant');
          }
        }
        
        // Initialize chat with welcome message if available
        if (initialMessage) {
          setMessages([{
            role: 'assistant',
            content: initialMessage
          }]);
        }
        
        setIsChanged(false);
      } catch (error) {
        console.error('Error fetching chatbot:', error);
        setError('Failed to load chatbot data');
      } finally {
        setIsLoading(false);
      }
    };

    if (chatbotId) {
      fetchChatbotData();
    }
  }, [chatbotId]);
  
  // Helper function to convert role name to value
  const getRoleValue = (roleName: string): string => {
    const role = roles.find(r => r.label.toLowerCase() === roleName.toLowerCase());
    return role ? role.value : 'assistant';
  };

  // Update instructions when role changes
  useEffect(() => {
    if (!isChanged) {
      setInstructions(rolePrompts[role] || '');
    }
  }, [role]);

  // Mark as changed when any config option changes
  useEffect(() => {
    setIsChanged(true);
  }, [name, description, instructions, temperature, primaryColor, position, initialMessage, maxTokens, enableMemory, memoryWindow, chatTitle, secondaryColor, showBranding]);

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

  const previewModes = [
    { value: 'desktop', label: 'Desktop' },
    { value: 'mobile', label: 'Mobile' },
  ];

  // Scroll to bottom of chat container when messages change
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const newMessage = {
      role: 'user' as const,
      content: inputMessage
    };

    setMessages(prev => [...prev, newMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      // Get auth token
      const token = localStorage.getItem('auth_token');
      if (!token) {
        console.error('No auth token found');
        throw new Error('Authentication required');
      }

      // Prepare settings for preview request
      const previewSettings = {
        temperature: temperature[0],
        maxTokens: maxTokens[0],
        model: "llama3-70b-8192",
        instructions: instructions,
        role: roles.find(r => r.value === role)?.label || ''
      };

      // Call the preview endpoint
      console.log('Sending preview request with settings:', previewSettings);
      console.log('Sending documents for preview:', documents);
      const response = await fetch('http://localhost:8000/api/chatbots/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          message: inputMessage,
          settings: previewSettings,
          chatHistory: messages.map(msg => ({
            role: msg.role,
            content: msg.content
          })),
          documents: documents || [], // Include any documents associated with the chatbot
          chatbotId: chatbotId // Add chatbotId here
        }),
      });

      if (!response.ok) {
        console.error('Preview response error:', response.status);
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`Failed to get response: ${response.status}`);
      }

      const data = await response.json();
      console.log('Received preview response:', data);
      
      // Add response to chat
      const aiResponse = {
        role: 'assistant' as const,
        content: data.response,
        sources: data.sources
      };
      
      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      console.error('Error getting preview response:', error);
      
      // Handle error with fallback response
      const errorResponse = {
        role: 'assistant' as const,
        content: 'I apologize, but I encountered an error while processing your request. Please try again.'
      };
      
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setMessages([]);
    if (initialMessage) {
      setTimeout(() => {
        setMessages([{
          role: 'assistant',
          content: initialMessage
        }]);
      }, 300);
    }
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);
      const token = localStorage.getItem('auth_token');
      if (!token) {
        console.error('No auth token found');
        throw new Error('Authentication required');
      }

      // First do a simple GET request to test authentication
      console.log('Testing authentication...');
      const testAuth = await fetch(`http://localhost:8000/api/chatbots/${chatbotId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      
      if (!testAuth.ok) {
        console.error('Auth test failed:', testAuth.status);
        const errorText = await testAuth.text();
        console.error('Auth test error response:', errorText);
        throw new Error(`Authentication test failed: ${testAuth.status}`);
      }

      console.log('Auth test successful, proceeding with update...');
      
      // Now proceed with the update
      const updateData = {
        name,
        description,
        settings: {
          temperature: temperature[0],
          maxTokens: maxTokens[0],
          instructions,
          role: roles.find(r => r.value === role)?.label || '',
          model: "llama3-70b-8192", // Default model or get from state if you have it
          appearance: {
            primaryColor,
            secondaryColor,
            position,
            chatTitle,
            showBranding,
            initialMessage
          }
        },
        documents: documents
      };
      
      console.log('Sending update with data:', JSON.stringify(updateData, null, 2));
      
      const response = await fetch(`http://localhost:8000/api/chatbots/${chatbotId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) {
        console.error('Update failed:', response.status);
        const errorText = await response.text();
        console.error('Update error response:', errorText);
        throw new Error(`Failed to update chatbot: ${response.status}`);
      }

      console.log('Chatbot updated successfully');
      
      // Show temporary success notification
      const notification = document.createElement('div');
      notification.className = 'fixed bottom-4 right-4 bg-green-500 text-white px-4 py-2 rounded shadow-lg';
      notification.textContent = 'Chatbot settings saved successfully!';
      document.body.appendChild(notification);
      setTimeout(() => {
        notification.remove();
      }, 3000);
      
    } catch (error) {
      console.error('Error saving chatbot:', error);
      
      // Show temporary error notification
      const notification = document.createElement('div');
      notification.className = 'fixed bottom-4 right-4 bg-red-500 text-white px-4 py-2 rounded shadow-lg';
      notification.textContent = `Failed to save: ${error instanceof Error ? error.message : 'Unknown error'}`;
      document.body.appendChild(notification);
      setTimeout(() => {
        notification.remove();
      }, 5000);
      
    } finally {
      setIsSaving(false);
    }
  };

  const handleCopyEmbedCode = () => {
    // Create the full embed code with proper script attributes
    const origin = window.location.origin;
    const embedCode = `<script 
  src="${origin}/widget/${chatbotId}" 
  data-chatbot-id="${chatbotId}"
  data-position="${position}"
  data-primary-color="${primaryColor.replace('#', '')}"
  data-title="${chatTitle}"
  data-show-branding="${showBranding}"
></script>`;

    // Copy to clipboard
    navigator.clipboard.writeText(embedCode);
    
    // Feedback
    setIsCopied(true);
    setTimeout(() => setIsCopied(false), 2000);
    
    // For testing, log the embed code
    console.log('Generated embed code:', embedCode);
    
    // Simulate the embed script working
    const testEmbed = document.createElement('div');
    testEmbed.className = 'fixed bottom-20 right-4 bg-green-100 text-green-800 p-3 rounded shadow-md text-sm';
    testEmbed.innerHTML = `
      <p class="font-medium">✅ Embed code copied!</p>
      <p class="text-xs mt-1">Widget will appear in the ${position} position with the title "${chatTitle}"</p>
    `;
    document.body.appendChild(testEmbed);
    setTimeout(() => {
      document.body.removeChild(testEmbed);
    }, 5000);
  };

  const handlePreviewEmbed = () => {
    // Remove any existing preview widget
    const existingWidget = document.getElementById('test-widget-script');
    if (existingWidget) {
      document.body.removeChild(existingWidget);
    }
    
    // Create and append the widget script
    const widgetScript = document.createElement('script');
    widgetScript.id = 'test-widget-script';
    
    // Use the backend URL directly
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const widgetUrl = `${backendUrl}/widget/${chatbotId}.js`;
    widgetScript.src = widgetUrl;
    
    // Add debugging console log
    console.log('Attempting to load widget script:', {
      url: widgetUrl,
      chatbotId,
      backendUrl
    });
    
    widgetScript.setAttribute('data-chatbot-id', chatbotId);
    widgetScript.setAttribute('data-position', position);
    widgetScript.setAttribute('data-primary-color', primaryColor.replace('#', ''));
    widgetScript.setAttribute('data-title', chatTitle);
    widgetScript.setAttribute('data-show-branding', showBranding.toString());
    
    // Add notification
    const notification = document.createElement('div');
    notification.id = 'widget-test-notification';
    notification.className = 'fixed top-20 right-4 bg-blue-100 text-blue-800 p-3 rounded shadow-md text-sm z-50';
    notification.innerHTML = `
      <p class="font-medium">Testing widget...</p>
      <p class="text-xs mt-1">The chatbot widget should appear at the ${position} of the page</p>
      <button id="remove-test-widget" class="mt-2 text-xs bg-blue-500 text-white px-2 py-1 rounded">Remove Test Widget</button>
    `;
    document.body.appendChild(notification);
    
    // Add event listener to remove button
    setTimeout(() => {
      const removeButton = document.getElementById('remove-test-widget');
      if (removeButton) {
        removeButton.addEventListener('click', () => {
          const existingWidget = document.getElementById('test-widget-script');
          if (existingWidget) document.body.removeChild(existingWidget);
          const notification = document.getElementById('widget-test-notification');
          if (notification) document.body.removeChild(notification);
        });
      }
    }, 100);
    
    // Add event listener to detect script load errors
    widgetScript.onerror = (e) => {
      console.error('Failed to load widget script:', {
        error: e,
        url: widgetUrl,
        chatbotId,
        backendUrl
      });
      
      const errorNotification = document.createElement('div');
      errorNotification.className = 'fixed bottom-4 right-4 bg-red-100 text-red-800 p-3 rounded shadow-md text-sm z-50';
      errorNotification.innerHTML = `
        <p class="font-medium">Error loading widget</p>
        <p class="text-xs mt-1">Please check:</p>
        <ul class="text-xs list-disc list-inside mt-1">
          <li>Backend server is running on ${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8080'}</li>
          <li>Chatbot ID ${chatbotId} exists</li>
          <li>Widget script is accessible at ${widgetUrl}</li>
        </ul>
        <p class="text-xs mt-2">Check browser console for more details.</p>
      `;
      document.body.appendChild(errorNotification);
      setTimeout(() => {
        if (errorNotification.parentNode) {
          document.body.removeChild(errorNotification);
        }
      }, 10000);
    };
    
    // Add event listener to detect script load success
    widgetScript.onload = () => {
      console.log('Widget script loaded successfully');
    };
    
    // Append the script to load the widget
    document.body.appendChild(widgetScript);
  };

  // Initialize with welcome message if set
  useEffect(() => {
    if (initialMessage && messages.length === 0) {
      setMessages([{
        role: 'assistant',
        content: initialMessage
      }]);
    }
  }, [initialMessage]);

  // Generate a preview of the chatbot configuration
  const chatbotPreview = () => {
    // Mobile preview has a different width
    const previewWidth = previewMode === 'mobile' ? 'w-[350px]' : 'w-full';
    const previewHeight = previewMode === 'mobile' ? 'h-[600px]' : 'h-[500px]';
    
    return (
      <div className={`border rounded-lg overflow-hidden ${previewWidth} mx-auto ${previewHeight} flex flex-col`}>
        {/* Chat header */}
        <div 
          className="p-3 border-b flex items-center justify-between"
          style={{ backgroundColor: primaryColor, color: '#fff' }}
        >
          <div className="font-medium">{chatTitle}</div>
        </div>
        
        {/* Chat messages */}
        <div 
          ref={chatContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-4 bg-background"
        >
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 ${
                  message.role === 'user'
                    ? 'text-white ml-4'
                    : 'bg-muted mr-4'
                }`}
                style={{
                  backgroundColor: message.role === 'user' ? primaryColor : undefined
                }}
              >
                {message.content}
                
                {/* Display sources if available */}
                {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-xs font-medium mb-1">Sources:</p>
                    <div className="space-y-1">
                      {message.sources.map((source, i) => (
                        <div key={i} className="text-xs flex items-center">
                          <span className="inline-block w-3 h-3 rounded-full bg-green-500 mr-2 
                            opacity-80" style={{ opacity: Math.max(0.3, source.score) }}></span>
                          <span>
                            {source.document_id 
                              ? `Document: ${source.document_id.substring(0, 8)}...` 
                              : 'Unknown document'
                            }
                            {source.score ? ` (${(source.score * 100).toFixed(1)}% match)` : ''}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
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
        
        {/* Chat input */}
        <div className="p-3 border-t bg-background">
          <div className="flex gap-2">
            <Input
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Type your message..."
              className="flex-1"
            />
            <Button 
              onClick={handleSendMessage} 
              disabled={isLoading}
              style={{ backgroundColor: primaryColor }}
            >
              <SendIcon size={18} />
            </Button>
          </div>
          {showBranding && (
            <div className="text-xs text-center mt-2 text-muted-foreground">
              Powered by ChatSphere
            </div>
          )}
        </div>
      </div>
    );
  };

  // Render loading state while fetching data
  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background">
        <div className="animate-spin h-12 w-12 border-4 border-primary border-t-transparent rounded-full mb-4"></div>
        <h2 className="text-xl font-medium mb-2">Loading Chatbot...</h2>
        <p className="text-muted-foreground">Please wait while we fetch your chatbot configuration.</p>
      </div>
    );
  }
  
  // Render error state if there was a problem
  if (error) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background">
        <div className="p-8 max-w-md w-full bg-destructive/10 rounded-lg text-center">
          <h2 className="text-xl font-medium mb-4 text-destructive">Error Loading Chatbot</h2>
          <p className="text-foreground mb-6">{error}</p>
          <div className="flex space-x-4 justify-center">
            <button 
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md"
            >
              Try Again
            </button>
            <button 
              onClick={() => router.push('/dashboard/chatbots')}
              className="px-4 py-2 bg-muted text-foreground rounded-md"
            >
              Back to Chatbots
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="container mx-auto px-4 py-8 max-w-7xl"
    >
      <div className="flex justify-between items-center mb-6">
        <motion.h1
          initial={{ y: -20 }}
          animate={{ y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-2xl font-bold"
        >
          Chatbot Configuration
        </motion.h1>
        
        <div className="flex space-x-3">
          <Button 
            variant="outline" 
            onClick={handleReset}
            className="flex items-center gap-2"
          >
            <RefreshCw size={16} />
            Reset Preview
          </Button>
          
          <Button 
            onClick={handleSave} 
            disabled={isSaving || !isChanged}
            className="flex items-center gap-2"
          >
            {isSaving ? (
              <>
                <RefreshCw size={16} className="animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save size={16} />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>
      
      {isChanged && (
        <motion.div 
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200 p-3 rounded-md mb-6 flex items-center gap-2"
        >
          <InfoIcon size={16} />
          <span>You have unsaved changes. Don't forget to save before leaving this page.</span>
        </motion.div>
      )}
      
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Configuration Options - Takes 3/5 of the space */}
        <div className="lg:col-span-3 space-y-6">
          <Tabs defaultValue="basic" onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid grid-cols-3 mb-6">
              <TabsTrigger value="basic">Basic Settings</TabsTrigger>
              <TabsTrigger value="advanced">Advanced Settings</TabsTrigger>
              <TabsTrigger value="appearance">Appearance</TabsTrigger>
            </TabsList>
            
            <TabsContent value="basic" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Basic Information</CardTitle>
                  <CardDescription>Configure the core settings for your chatbot</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="name">Name</Label>
                    <Input
                      id="name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Enter chatbot name"
                    />
                    <p className="text-sm text-muted-foreground">This name will be used internally to identify your chatbot</p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="description">Description</Label>
                    <Textarea
                      id="description"
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      placeholder="Enter chatbot description"
                      rows={3}
                    />
                    <p className="text-sm text-muted-foreground">A brief description of what this chatbot does</p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="role">Role Template</Label>
                    <Select
                      id="role"
                      value={role}
                      onValueChange={setRole}
                      options={roles}
                    />
                    <p className="text-sm text-muted-foreground">Select a pre-defined role to use as a starting point</p>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>System Instructions</CardTitle>
                  <CardDescription>Define how your chatbot should behave and respond</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <Label htmlFor="instructions">Custom System Prompt</Label>
                    <Textarea
                      id="instructions"
                      value={instructions}
                      onChange={(e) => setInstructions(e.target.value)}
                      placeholder="Enter system instructions"
                      className="h-40 font-mono text-sm"
                    />
                    <div className="flex justify-between">
                      <p className="text-sm text-muted-foreground">These instructions tell the AI how to behave</p>
                      <p className="text-sm text-muted-foreground">{instructions.length} characters</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="advanced" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Model Parameters</CardTitle>
                  <CardDescription>Fine-tune the AI model's behavior</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <Label htmlFor="temperature">Temperature: {temperature[0].toFixed(1)}</Label>
                      <Badge variant={temperature[0] < 0.3 ? "secondary" : temperature[0] > 0.7 ? "destructive" : "default"}>
                        {temperature[0] < 0.3 ? "Focused" : temperature[0] > 0.7 ? "Creative" : "Balanced"}
                      </Badge>
                    </div>
                    <Slider
                      id="temperature"
                      value={temperature}
                      onValueChange={setTemperature}
                      min={0}
                      max={1}
                      step={0.1}
                    />
                    <p className="text-sm text-muted-foreground">
                      Lower values produce more consistent, deterministic responses. Higher values produce more varied, creative responses.
                    </p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="maxTokens">Max Response Length: {maxTokens[0]}</Label>
                    <Slider
                      id="maxTokens"
                      value={maxTokens}
                      onValueChange={setMaxTokens}
                      min={256}
                      max={4096}
                      step={256}
                    />
                    <p className="text-sm text-muted-foreground">
                      Maximum number of tokens (words/characters) in each response
                    </p>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Conversation Settings</CardTitle>
                  <CardDescription>Configure how conversations work</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="initialMessage">Initial Message</Label>
                    <Textarea
                      id="initialMessage"
                      value={initialMessage}
                      onChange={(e) => setInitialMessage(e.target.value)}
                      placeholder="Enter an optional welcome message"
                      rows={3}
                    />
                    <p className="text-sm text-muted-foreground">This message will be shown when a user first opens the chat</p>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="enableMemory">Conversation Memory</Label>
                      <p className="text-sm text-muted-foreground">Remember previous messages in the conversation</p>
                    </div>
                    <Switch
                      id="enableMemory"
                      checked={enableMemory}
                      onCheckedChange={setEnableMemory}
                    />
                  </div>
                  
                  {enableMemory && (
                    <div className="space-y-2">
                      <Label htmlFor="memoryWindow">Memory Window: {memoryWindow[0]} messages</Label>
                      <Slider
                        id="memoryWindow"
                        value={memoryWindow}
                        onValueChange={setMemoryWindow}
                        min={1}
                        max={20}
                        step={1}
                      />
                      <p className="text-sm text-muted-foreground">
                        Number of previous messages to remember
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
            
            <TabsContent value="appearance" className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Visual Appearance</CardTitle>
                  <CardDescription>Customize how your chatbot looks</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <Label htmlFor="chatTitle">Chat Window Title</Label>
                    <Input
                      id="chatTitle"
                      value={chatTitle}
                      onChange={(e) => setChatTitle(e.target.value)}
                      placeholder="Enter chat window title"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="primaryColor">Primary Color</Label>
                    <div className="flex gap-4 items-center">
                      <Input
                        type="color"
                        id="primaryColor"
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
                    <p className="text-sm text-muted-foreground">Used for user messages, buttons, and accents</p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="secondaryColor">Secondary Color</Label>
                    <div className="flex gap-4 items-center">
                      <Input
                        type="color"
                        id="secondaryColor"
                        value={secondaryColor}
                        onChange={(e) => setSecondaryColor(e.target.value)}
                        className="w-20 h-10"
                      />
                      <Input
                        type="text"
                        value={secondaryColor}
                        onChange={(e) => setSecondaryColor(e.target.value)}
                        className="flex-1"
                      />
                    </div>
                    <p className="text-sm text-muted-foreground">Used for background elements</p>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="position">Widget Position</Label>
                    <Select
                      id="position"
                      value={position}
                      onValueChange={setPosition}
                      options={positions}
                    />
                    <p className="text-sm text-muted-foreground">Where the chat widget appears on your website</p>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label htmlFor="showBranding">Show Branding</Label>
                      <p className="text-sm text-muted-foreground">Display "Powered by ChatSphere" in the widget</p>
                    </div>
                    <Switch
                      id="showBranding"
                      checked={showBranding}
                      onCheckedChange={setShowBranding}
                    />
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardHeader>
                  <CardTitle>Preview Mode</CardTitle>
                  <CardDescription>Switch between desktop and mobile views</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-4">
                    {previewModes.map((mode) => (
                      <Button
                        key={mode.value}
                        variant={previewMode === mode.value ? "default" : "outline"}
                        onClick={() => setPreviewMode(mode.value)}
                        className="flex items-center gap-2"
                      >
                        {mode.value === 'desktop' ? <Monitor size={16} /> : <Smartphone size={16} />}
                        {mode.label}
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
          
          <Card>
            <CardHeader>
              <CardTitle>Embed Your Chatbot</CardTitle>
              <CardDescription>Add this code to your website to display the chatbot</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 mt-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-medium">Embed Code</h3>
                  <Button variant="outline" size="sm" onClick={handlePreviewEmbed}>
                    Preview Widget
                  </Button>
                </div>
                <div className="relative">
                  <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto">
                    {`<script 
  src="${window.location.origin}/widget/${chatbotId}" 
  data-chatbot-id="${chatbotId}"
  data-position="${position}"
  data-primary-color="${primaryColor.replace('#', '')}"
  data-title="${chatTitle}"
  data-show-branding="${showBranding}"
></script>`}
                  </pre>
                </div>
              </div>
            </CardContent>
            <CardFooter>
              <Button 
                variant="outline" 
                className="w-full flex items-center gap-2"
                onClick={handleCopyEmbedCode}
              >
                {isCopied ? <Check size={16} /> : <Copy size={16} />}
                {isCopied ? 'Copied!' : 'Copy Embed Code'}
              </Button>
            </CardFooter>
          </Card>
        </div>
        
        {/* Preview - Takes 2/5 of the space */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader className="pb-0">
              <CardTitle>Live Preview</CardTitle>
              <CardDescription>See how your chatbot will appear to users</CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="flex justify-center">
                {chatbotPreview()}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </motion.div>
  );
}