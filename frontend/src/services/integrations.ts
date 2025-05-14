import { getAuthToken } from '@/lib/auth';

const API_BASE_URL = 'http://localhost:8000/api';

export interface IntegrationConfig {
  webhookUrl?: string;
  botToken?: string;
  signingSecret?: string;
  error?: string;
}

export interface Integration {
  id: string;
  type: 'slack' | 'discord' | 'website' | 'email';
  name: string;
  status: 'pending' | 'active' | 'error';
  userId: string;
  chatbotId: string;
  config: IntegrationConfig;
  createdAt: string;
  updatedAt: string;
}

export async function createIntegration(type: string, data: {
  name: string;
  chatbotId: string;
  config: IntegrationConfig;
}): Promise<Integration> {
  const token = getAuthToken();
  if (!token) throw new Error('Not authenticated');

  const response = await fetch(`${API_BASE_URL}/integrations/${type}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error);
  }

  return response.json();
}

export async function updateSlackCredentials(integrationId: string, credentials: {
  webhookUrl: string;
  botToken: string;
  signingSecret: string;
}): Promise<Integration> {
  const token = getAuthToken();
  if (!token) throw new Error('Not authenticated');

  const response = await fetch(`${API_BASE_URL}/integrations/slack/${integrationId}/credentials`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error);
  }

  return response.json();
}

export async function getIntegration(integrationId: string): Promise<Integration> {
  const token = getAuthToken();
  if (!token) throw new Error('Not authenticated');

  const response = await fetch(`${API_BASE_URL}/integrations/${integrationId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error);
  }

  return response.json();
}

export async function listIntegrations(): Promise<Integration[]> {
  const token = getAuthToken();
  if (!token) throw new Error('Not authenticated');

  const response = await fetch(`${API_BASE_URL}/integrations`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error);
  }

  return response.json();
}

export async function deleteIntegration(integrationId: string): Promise<void> {
  const token = getAuthToken();
  if (!token) throw new Error('Not authenticated');

  const response = await fetch(`${API_BASE_URL}/integrations/${integrationId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error);
  }
}

export async function updateIntegration(integrationId: string, data: {
  name?: string;
  status?: 'active' | 'inactive' | 'pending';
  chatbotId?: string;
  config?: IntegrationConfig;
}): Promise<Integration> {
  const token = getAuthToken();
  if (!token) throw new Error('Not authenticated');

  const response = await fetch(`${API_BASE_URL}/integrations/${integrationId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error);
  }

  return response.json();
} 