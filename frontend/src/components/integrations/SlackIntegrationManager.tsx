'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, CheckCircle2, Plus } from 'lucide-react';
import { SlackIntegrationSettings } from './SlackIntegrationSettings';
import { Integration, createIntegration, updateIntegration } from '@/services/integrations';
import { Badge } from '@/components/ui/badge';

interface SlackIntegrationManagerProps {
  integration?: Integration;
  onUpdate: (integration: Integration) => void;
}

export function SlackIntegrationManager({ integration, onUpdate }: SlackIntegrationManagerProps) {
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    try {
      setIsCreating(true);
      setError(null);
      const newIntegration = await createIntegration('slack', {
        name: 'Slack Integration',
        type: 'slack',
        config: {}
      });
      onUpdate(newIntegration);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create Slack integration');
    } finally {
      setIsCreating(false);
    }
  };

  const handleSaveCredentials = async (credentials: {
    webhookUrl: string;
    botToken: string;
    signingSecret: string;
  }) => {
    if (!integration) return;

    try {
      setError(null);
      const updatedIntegration = await updateIntegration(integration.id, {
        config: {
          ...integration.config,
          ...credentials
        },
        status: 'pending' // Reset status to pending when credentials change
      });
      onUpdate(updatedIntegration);
    } catch (err) {
      throw err;
    }
  };

  const renderStatusBadge = () => {
    if (!integration) return <Badge variant="outline">Not Configured</Badge>;
    switch (integration.status) {
      case 'active':
        return <Badge variant="success"><CheckCircle2 className="h-3 w-3 mr-1"/> Active</Badge>;
      case 'pending':
        return <Badge variant="secondary">Pending Verification</Badge>;
      case 'error':
        return <Badge variant="destructive"><AlertCircle className="h-3 w-3 mr-1"/> Error</Badge>;
      default:
        return <Badge variant="outline">{integration.status}</Badge>;
    }
  };

  if (!integration) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Add Slack Integration</CardTitle>
          <CardDescription>
            Connect your chatbot to Slack to enable notifications and chat functionality.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          <p className="text-sm text-muted-foreground mb-4">
            Adding a Slack integration will allow you to:
            <ul className="list-disc list-inside mt-2 space-y-1">
              <li>Receive notifications when your chatbot needs assistance</li>
              <li>Chat with your bot directly in Slack</li>
              <li>Forward unhandled queries to your team</li>
            </ul>
          </p>
        </CardContent>
        <CardFooter>
          <Button onClick={handleCreate} disabled={isCreating}>
            <Plus className="w-4 h-4 mr-2" />
            {isCreating ? 'Adding...' : 'Add Slack Integration'}
          </Button>
        </CardFooter>
      </Card>
    );
  }

  return (
    <SlackIntegrationSettings
      integrationId={integration.id}
      config={integration.config}
      onSave={handleSaveCredentials}
    />
  );
} 