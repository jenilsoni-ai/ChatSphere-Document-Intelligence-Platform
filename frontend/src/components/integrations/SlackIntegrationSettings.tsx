'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';

interface SlackIntegrationSettingsProps {
  integrationId: string;
  config?: {
    webhookUrl?: string;
    botToken?: string;
    signingSecret?: string;
    error?: string;
  };
  onSave: (credentials: { webhookUrl: string; botToken: string; signingSecret: string }) => Promise<void>;
}

export function SlackIntegrationSettings({ integrationId, config, onSave }: SlackIntegrationSettingsProps) {
  const [webhookUrl, setWebhookUrl] = useState(config?.webhookUrl || '');
  const [botToken, setBotToken] = useState(config?.botToken || '');
  const [signingSecret, setSigningSecret] = useState(config?.signingSecret || '');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(config?.error || '');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError('');
    setSuccess(false);

    try {
      await onSave({
        webhookUrl,
        botToken,
        signingSecret
      });
      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save Slack integration settings');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Slack Integration Settings</CardTitle>
        <CardDescription>
          Configure your Slack integration to enable notifications and chat functionality.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="webhookUrl">Webhook URL</Label>
            <Input
              id="webhookUrl"
              placeholder="https://hooks.slack.com/services/..."
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              required
            />
            <p className="text-xs text-muted-foreground">
              Create a new Slack app and add an incoming webhook to get this URL.
            </p>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="botToken">Bot User OAuth Token</Label>
            <Input
              id="botToken"
              placeholder="xoxb-..."
              value={botToken}
              onChange={(e) => setBotToken(e.target.value)}
              required
            />
            <p className="text-xs text-muted-foreground">
              Get this from your Slack app's OAuth & Permissions page.
            </p>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="signingSecret">Signing Secret</Label>
            <Input
              id="signingSecret"
              placeholder="Enter your Slack app signing secret"
              value={signingSecret}
              onChange={(e) => setSigningSecret(e.target.value)}
              required
            />
            <p className="text-xs text-muted-foreground">
              Get this from your Slack app's Basic Information page.
            </p>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {success && (
            <Alert>
              <CheckCircle2 className="h-4 w-4" />
              <AlertTitle>Success</AlertTitle>
              <AlertDescription>Slack integration settings saved successfully.</AlertDescription>
            </Alert>
          )}
        </form>
      </CardContent>
      <CardFooter>
        <Button 
          onClick={handleSubmit} 
          disabled={isSaving || !webhookUrl || !botToken || !signingSecret}
        >
          {isSaving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isSaving ? 'Saving...' : 'Save Settings'}
        </Button>
      </CardFooter>
    </Card>
  );
} 