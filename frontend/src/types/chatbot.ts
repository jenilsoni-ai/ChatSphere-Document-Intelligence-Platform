export interface AppearanceSettings {
  primaryColor: string;
  secondaryColor: string;
  position: string;
  chatTitle: string;
  showBranding: boolean;
  initialMessage?: string;
}

export interface ChatbotSettings {
  temperature: number;
  maxTokens: number;
  model: string;
  instructions: string;
  role: string;
  appearance?: AppearanceSettings;
}

export interface Chatbot {
  id: string;
  name: string;
  description: string;
  settings: ChatbotSettings;
  ownerId: string;
  documents: string[];
  createdAt: string;
  updatedAt: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
}

export interface PreviewRequest {
  message: string;
  settings: ChatbotSettings;
  chatHistory: ChatMessage[];
}

export interface PreviewResponse {
  response: string;
  sources?: Array<{
    documentId: string;
    chunkId: string;
    score: number;
  }>;
} 