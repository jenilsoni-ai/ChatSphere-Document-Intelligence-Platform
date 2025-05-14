'use client';

import React, { useState, useEffect } from 'react';
import { Integration, createIntegration, updateIntegration } from '@/services/integrations';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { InfoIcon, CheckCircle, XCircle, Clock, LinkIcon, Loader2 } from 'lucide-react';
import { useToast } from '@/components/ui/use-toast';
import { Badge } from '@/components/ui/badge';

interface WebsiteIntegrationManagerProps {
  integration?: Integration;
  onUpdate: (integration: Integration) => void;
}

export function WebsiteIntegrationManager({ integration: initialIntegration, onUpdate }: WebsiteIntegrationManagerProps) {
  const [integration, setIntegration] = useState<Integration | undefined>(initialIntegration);
  const [domain, setDomain] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    setIntegration(initialIntegration);
    setDomain(initialIntegration?.config?.domain || '');
  }, [initialIntegration]);

  const handleSave = async () => {
    if (!domain) {
      toast({ title: "Error", description: "Domain name is required.", variant: "destructive" });
      return;
    }

    setIsLoading(true);
    try {
      let updatedIntegration;
      if (integration) {
        // Update existing integration
        updatedIntegration = await updateIntegration(integration.id, {
          config: { ...integration.config, domain },
          status: 'pending' // Reset status to pending when domain changes
        });
        toast({ title: "Success", description: "Website integration updated." });
      } else {
        // Create new integration
        updatedIntegration = await createIntegration('website', {
          name: `${domain} Integration`,
          type: 'website',
          config: { domain }
        });
        toast({ title: "Success", description: "Website integration created. Verification pending." });
      }
      onUpdate(updatedIntegration);
    } catch (error) {
      console.error("Failed to save website integration:", error);
      toast({ title: "Error", description: error instanceof Error ? error.message : "Failed to save integration.", variant: "destructive" });
    } finally {
      setIsLoading(false);
    }
  };

  const renderStatusBadge = () => {
    if (!integration) return <Badge variant="outline">Not Configured</Badge>;
    switch (integration.status) {
      case 'active':
        return <Badge variant="success"><CheckCircle className="h-3 w-3 mr-1"/> Active</Badge>;
      case 'pending':
        return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1"/> Pending Verification</Badge>;
      case 'configuring':
        return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1"/> Configuring DNS</Badge>;
      case 'error':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1"/> Error</Badge>;
      default:
        return <Badge variant="outline">{integration.status}</Badge>;
    }
  };

  const renderVerificationInfo = () => {
    if (!integration || integration.status !== 'pending' || !integration.config?.verification) {
      return null;
    }
    const { type, name, value } = integration.config.verification;
    return (
      <Alert className="mt-4">
        <InfoIcon className="h-4 w-4" />
        <AlertTitle>Verify Your Domain</AlertTitle>
        <AlertDescription>
          <p>To activate the website integration, please add the following DNS record to your domain registrar:</p>
          <div className="mt-2 p-2 bg-muted rounded text-sm font-mono">
            <p>Type: {type}</p>
            <p>Name/Host: {name}</p>
            <p>Value/Content: {value}</p>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">DNS changes can take some time to propagate. We will automatically check for verification.</p>
        </AlertDescription>
      </Alert>
    );
  };

  const renderSetupInfo = () => {
    if (!integration || integration.status !== 'configuring' || !integration.config?.setup) {
      return null;
    }
    const { cnameRecord } = integration.config.setup;
    return (
      <Alert className="mt-4" variant="default">
        <InfoIcon className="h-4 w-4" />
        <AlertTitle>Configure Domain DNS</AlertTitle>
        <AlertDescription>
          <p>Your domain is verified! Now, point your domain to our service by adding the following CNAME record:</p>
          <div className="mt-2 p-2 bg-muted rounded text-sm font-mono">
            <p>Type: CNAME</p>
            <p>Name/Host: {cnameRecord?.name || 'www'}</p>
            <p>Value/Target: {cnameRecord?.value || '[Provided by Backend]'}</p>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">Once DNS propagates, the integration will become active.</p>
        </AlertDescription>
      </Alert>
    );
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle className="flex items-center"><LinkIcon className="h-5 w-5 mr-2"/> Website Integration</CardTitle>
          {renderStatusBadge()}
        </div>
        <CardDescription>
          Allow users to interact with your chatbot directly on your website domain.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="website-domain">Your Website Domain</Label>
          <Input 
            id="website-domain"
            placeholder="e.g., www.yourcompany.com" 
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            disabled={isLoading || (integration && integration.status !== 'inactive' && integration.status !== 'error')}
          />
          <p className="text-xs text-muted-foreground">
            Enter the domain where you want to host the chatbot.
            {integration && integration.status !== 'inactive' && integration.status !== 'error' && ' Domain cannot be changed once verification starts.'}
          </p>
        </div>
        
        {renderVerificationInfo()}
        {renderSetupInfo()}

        {integration?.status === 'error' && integration.config?.error && (
          <Alert variant="destructive">
            <XCircle className="h-4 w-4" />
            <AlertTitle>Configuration Error</AlertTitle>
            <AlertDescription>{integration.config.error}</AlertDescription>
          </Alert>
        )}
      </CardContent>
      <CardFooter>
        <Button 
          onClick={handleSave} 
          disabled={isLoading || (integration && integration.status !== 'inactive' && integration.status !== 'error' && !integration.config?.error)}
        >
          {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {integration ? 'Save Changes' : 'Setup Integration'}
        </Button>
      </CardFooter>
    </Card>
  );
} 