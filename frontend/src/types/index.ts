// Integration Types

export interface IntegrationProvider {
  id: string;
  name: string;
  description: string | null;
  type: 'knowledge_base' | 'notification' | 'analytics';
  icon_url: string | null;
  config_schema: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface UserIntegration {
  id: string;
  user_id: string;
  provider_id: string;
  name: string;
  config: Record<string, any>;
  status: 'pending' | 'active' | 'error' | 'disabled';
  error_message: string | null;
  last_sync_at: string | null;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface ChatbotIntegration {
  id: string;
  chatbot_id: string;
  integration_id: string;
  is_active: boolean;
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface IntegrationSyncHistory {
  id: string;
  integration_id: string;
  status: 'success' | 'error';
  records_synced: number;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
  duration: string | null;
  metadata?: Record<string, any>;
}

export interface IntegrationOAuthToken {
  id: string;
  integration_id: string;
  access_token: string;
  refresh_token: string | null;
  token_type: string | null;
  scope: string | null;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
} 