'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import { SlackIntegrationManager } from '@/components/integrations/SlackIntegrationManager';
import { WebsiteIntegrationManager } from '@/components/integrations/WebsiteIntegrationManager';
import { Integration, listIntegrations } from '@/services/integrations';

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const fetchIntegrations = async () => {
    try {
      setLoading(true);
      const data = await listIntegrations();
      setIntegrations(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load integrations');
    } finally {
      setLoading(false);
    }
  };

  const handleIntegrationUpdate = (updatedIntegration: Integration) => {
    setIntegrations(prev => {
      const existingIndex = prev.findIndex(i => i.id === updatedIntegration.id);
      if (existingIndex > -1) {
        const newIntegrations = [...prev];
        newIntegrations[existingIndex] = updatedIntegration;
        return newIntegrations;
      } else {
        return [...prev, updatedIntegration];
      }
    });
  };

  const slackIntegration = integrations.find(i => i.type === 'slack');
  const websiteIntegration = integrations.find(i => i.type === 'website');

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Integrations</h1>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {loading ? (
        <div>Loading integrations...</div>
      ) : (
        <Tabs defaultValue="slack" className="w-full">
          <TabsList>
            <TabsTrigger value="slack">Slack</TabsTrigger>
            <TabsTrigger value="website">Website</TabsTrigger>
          </TabsList>

          <TabsContent value="slack">
            <SlackIntegrationManager
              integration={slackIntegration}
              onUpdate={handleIntegrationUpdate}
            />
          </TabsContent>
          
          <TabsContent value="website">
            <WebsiteIntegrationManager
              integration={websiteIntegration}
              onUpdate={handleIntegrationUpdate}
            />
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}