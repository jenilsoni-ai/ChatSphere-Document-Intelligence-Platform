import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useToast } from '@/components/ui/use-toast';
import { VectorStoreSettings as VectorStoreSettingsType } from '@/types/api';

interface VectorStoreSettingsProps {
  onSave: (settings: VectorStoreSettingsType) => Promise<void>;
}

export function VectorStoreSettings({ onSave }: VectorStoreSettingsProps) {
  const [settings, setSettings] = useState<VectorStoreSettingsType>({
    type: 'zilliz',
    zilliz_uri: '',
    zilliz_api_key: '',
    qdrant_url: '',
    qdrant_api_key: ''
  });
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    // Load current settings
    const loadSettings = async () => {
      try {
        const response = await fetch('/api/settings/vector-store');
        if (response.ok) {
          const data = await response.json();
          setSettings({
            type: data.type || 'zilliz',
            zilliz_uri: data.zilliz_uri || '',
            zilliz_api_key: data.zilliz_api_key || '',
            qdrant_url: data.qdrant_url || '',
            qdrant_api_key: data.qdrant_api_key || ''
          });
        }
      } catch (error) {
        console.error('Failed to load vector store settings:', error);
      }
    };
    loadSettings();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Prepare data for saving, only include relevant fields for the selected type
      const settingsToSave: Partial<VectorStoreSettingsType> = { type: settings.type };
      if (settings.type === 'zilliz') {
        settingsToSave.zilliz_uri = settings.zilliz_uri;
        settingsToSave.zilliz_api_key = settings.zilliz_api_key;
      } else if (settings.type === 'qdrant') {
        settingsToSave.qdrant_url = settings.qdrant_url;
        settingsToSave.qdrant_api_key = settings.qdrant_api_key;
      }

      await onSave(settingsToSave as VectorStoreSettingsType);
      toast({
        title: "Settings saved",
        description: "Vector store settings have been updated successfully.",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save vector store settings.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Vector Store Settings</CardTitle>
        <CardDescription>
          Configure the vector database connection (Zilliz Cloud or Qdrant).
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="vector-store-type">Vector Store Type</Label>
          <Select 
            value={settings.type} 
            onValueChange={(value: 'zilliz' | 'qdrant') => setSettings({...settings, type: value})}
          >
            <SelectTrigger id="vector-store-type">
              <SelectValue placeholder="Select vector store type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="zilliz">Zilliz Cloud</SelectItem>
              <SelectItem value="qdrant">Qdrant</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {settings.type === 'zilliz' && (
          <>
            <div className="space-y-2">
              <Label htmlFor="zilliz-uri">Zilliz URI</Label>
              <Input
                id="zilliz-uri"
                value={settings.zilliz_uri}
                onChange={(e) => setSettings({...settings, zilliz_uri: e.target.value})}
                placeholder="Your Zilliz Cloud URI"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="zilliz-api-key">Zilliz API Key</Label>
              <Input
                id="zilliz-api-key"
                type="password"
                value={settings.zilliz_api_key}
                onChange={(e) => setSettings({...settings, zilliz_api_key: e.target.value})}
                placeholder="Your Zilliz Cloud API Key"
              />
            </div>
          </>
        )}

        {settings.type === 'qdrant' && (
          <>
            <div className="space-y-2">
              <Label htmlFor="qdrant-url">Qdrant URL</Label>
              <Input
                id="qdrant-url"
                value={settings.qdrant_url}
                onChange={(e) => setSettings({...settings, qdrant_url: e.target.value})}
                placeholder="Your Qdrant instance URL"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="qdrant-api-key">Qdrant API Key</Label>
              <Input
                id="qdrant-api-key"
                type="password"
                value={settings.qdrant_api_key}
                onChange={(e) => setSettings({...settings, qdrant_api_key: e.target.value})}
                placeholder="Your Qdrant API Key (optional)"
              />
            </div>
          </>
        )}

        <Button onClick={handleSave} disabled={isSaving}>
          {isSaving ? 'Saving...' : 'Save Settings'}
        </Button>
      </CardContent>
    </Card>
  );
} 