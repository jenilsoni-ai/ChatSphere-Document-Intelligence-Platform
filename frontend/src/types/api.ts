export interface Document {
  id: string;
  name: string;
  storageUri: string;
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed';
  chunkCount: number;
  error?: string;
  vectorIds?: string[];
  createdAt: string;
  updatedAt: string;
  metadata?: Record<string, unknown>;
  processingStats?: {
    downloadTime: number;
    processingTime: number;
    totalTime: number;
  };
}

export interface Chatbot {
  id: string;
  name: string;
  description?: string;
  documents: string[];
  settings: {
    temperature?: number;
    instructions?: string;
  };
  createdAt: string;
  updatedAt: string;
}

export interface ChatMessage {
  id: string;
  chatbotId: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: {
    documentId: string;
    chunkId: string;
    score: number;
  }[];
  metadata?: {
    temperature?: number;
    tokens?: number;
    sources?: {
      document_id: string;
      chunk_id: string;
      score: number;
    }[];
    rag_status?: string;
  };
  createdAt: string;
}

export interface ChatHistory {
  messages: ChatMessage[];
}

export interface User {
  id: string;
  email: string;
  name: string;
  createdAt: string;
  updatedAt: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface ErrorResponse {
  error: string;
  details?: Record<string, unknown>;
}

export interface VectorStoreSettings {
  type: 'zilliz' | 'qdrant';
  zilliz_uri?: string;
  zilliz_api_key?: string;
  qdrant_url?: string;
  qdrant_api_key?: string;
}