'use client';

import React, { useState } from 'react';
import { ChatMessage as ChatMessageType } from '@/types/api';
import { AlertCircle, Check, Info, Search, Zap } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface ChatMessageProps {
  message: ChatMessageType;
  isLoading?: boolean;
  userName?: string;
  botName?: string;
}

export function ChatMessage({ message, isLoading = false, userName = 'You', botName = 'Assistant' }: ChatMessageProps) {
  const [showSources, setShowSources] = useState(false);
  
  // Get RAG status
  const ragStatus = message.metadata?.rag_status || '';
  const sourcesAvailable = message.metadata?.sources && message.metadata.sources.length > 0;
  
  // Get total number of tokens used
  const tokens = message.metadata?.tokens || 0;
  
  // Get RAG status label and icon
  const getRagStatusInfo = () => {
    switch(ragStatus) {
      case 'rag_success':
        return { 
          label: 'Knowledge used', 
          icon: <Check className="h-3 w-3 text-green-500" />, 
          description: 'This response was generated using knowledge from documents.',
          variant: 'success'
        };
      case 'llm_fallback':
        return { 
          label: 'AI knowledge only', 
          icon: <Zap className="h-3 w-3 text-amber-500" />, 
          description: 'This response was generated using AI general knowledge only.',
          variant: 'warning'
        };
      case 'no_context_found':
        return { 
          label: 'No matches found', 
          icon: <Search className="h-3 w-3 text-slate-500" />, 
          description: 'No matching information was found in the documents.',
          variant: 'secondary'
        };
      case 'no_documents':
        return { 
          label: 'No documents', 
          icon: <Info className="h-3 w-3 text-blue-500" />, 
          description: 'No documents are associated with this chatbot.',
          variant: 'outline'
        };
      case 'error':
        return { 
          label: 'Error', 
          icon: <AlertCircle className="h-3 w-3 text-red-500" />, 
          description: 'An error occurred while searching documents.',
          variant: 'destructive'
        };
      default:
        return { 
          label: '', 
          icon: null, 
          description: '',
          variant: 'outline'
        };
    }
  };
  
  const { label, icon, description, variant } = getRagStatusInfo();
  
  return (
    <div className={cn(
      "flex flex-col gap-2 w-full max-w-5xl mx-auto",
      message.role === 'user' ? "items-end" : "items-start"
    )}>
      <div className={cn(
        "flex flex-col max-w-[80%] rounded-xl p-4",
        message.role === 'user' 
          ? "bg-primary text-primary-foreground" 
          : "bg-muted"
      )}>
        <div className="flex justify-between items-center mb-2">
          <span className="font-medium text-sm">
            {message.role === 'user' ? userName : botName}
          </span>
          {message.role === 'assistant' && label && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge variant={variant as any} className="flex items-center gap-1 text-xs px-2 py-0 h-5">
                    {icon}
                    <span>{label}</span>
                  </Badge>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="max-w-xs">{description}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
        
        <div className="prose prose-sm dark:prose-invert max-w-none">
          {isLoading && message.role === 'assistant' ? (
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-current rounded-full animate-pulse" />
              <div className="w-2 h-2 bg-current rounded-full animate-pulse delay-100" />
              <div className="w-2 h-2 bg-current rounded-full animate-pulse delay-200" />
            </div>
          ) : (
            message.content
          )}
        </div>
        
        {/* Sources section - only show for assistant messages with sources */}
        {message.role === 'assistant' && sourcesAvailable && (
          <div className="mt-2">
            <div className="flex justify-between items-center">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setShowSources(!showSources)}
                className="text-xs px-2 py-1 h-auto"
              >
                {showSources ? 'Hide sources' : 'Show sources'}
              </Button>
              
              {tokens > 0 && (
                <span className="text-xs text-muted-foreground">
                  {tokens} tokens
                </span>
              )}
            </div>
            
            {showSources && (
              <div className="mt-2 pt-2 border-t border-border">
                <h4 className="text-xs font-semibold mb-1">Sources:</h4>
                <div className="space-y-1 max-h-32 overflow-y-auto">
                  {message.metadata?.sources.map((source, i) => (
                    <div key={i} className="text-xs flex items-center gap-2">
                      <span 
                        className="inline-block w-2 h-2 rounded-full bg-green-500" 
                        style={{ 
                          opacity: Math.max(0.3, source.score || 0)
                        }}
                      />
                      <span>
                        {source.document_id 
                          ? `${source.document_id.substring(0, 8)}...` 
                          : 'Unknown source'
                        }
                        {source.score ? ` (${(source.score * 100).toFixed(1)}% match)` : ''}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 