'use client';

import React, { useState, useEffect } from 'react';
import { PlusIcon, DocumentTextIcon, TrashIcon, GlobeAltIcon } from '@heroicons/react/24/outline';
import { documentsAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/components/ui/use-toast';
import { Progress } from "@/components/ui/progress";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip";
import { AlertCircle } from "lucide-react";

interface Document {
  id: string;
  name: string;
  storageUri: string;
  processingStatus: 'pending' | 'processing' | 'completed' | 'failed';
  chunkCount?: number;
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

function DocumentStatusBadge({ status, error }: { status: string; error?: string }) {
  const getStatusColor = () => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-500';
      case 'processing':
        return 'bg-blue-500 animate-pulse';
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="flex items-center gap-2">
      <span className={`h-2 w-2 rounded-full ${getStatusColor()}`} />
      <span className="text-sm capitalize">{status}</span>
      {error && status === 'failed' && (
        <Tooltip>
          <TooltipTrigger>
            <AlertCircle className="h-4 w-4 text-red-500" />
          </TooltipTrigger>
          <TooltipContent>{error}</TooltipContent>
        </Tooltip>
      )}
    </div>
  );
}

function ProcessingStats({ stats }: { stats?: Document['processingStats'] }) {
  if (!stats) return null;

  return (
    <div className="mt-2 text-sm text-gray-500">
      <div>Download: {(stats.downloadTime / 1000).toFixed(2)}s</div>
      <div>Processing: {(stats.processingTime / 1000).toFixed(2)}s</div>
      <div>Total: {(stats.totalTime / 1000).toFixed(2)}s</div>
    </div>
  );
}

export default function DataSourcesPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isUploadDialogOpen, setIsUploadDialogOpen] = useState(false);
  const [uploadMethod, setUploadMethod] = useState<'file' | 'url' | 'qa' | 'existing' | null>(null);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [url, setUrl] = useState('');
  const [documentName, setDocumentName] = useState('');
  const [documentDescription, setDocumentDescription] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await documentsAPI.list();
      setDocuments(data);
    } catch (err) {
      console.error('Error fetching documents:', err);
      setError('Failed to load data sources');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setUploadFile(file);
      
      // Auto-fill name if not already set
      if (!documentName) {
        setDocumentName(file.name.split('.')[0]);
      }
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (uploadMethod === 'file' && !uploadFile) {
      toast({
        title: "No file selected",
        description: "Please select a file to upload",
        variant: "destructive"
      });
      return;
    }

    if (uploadMethod === 'url' && !url) {
      toast({
        title: "No URL provided",
        description: "Please enter a website URL",
        variant: "destructive"
      });
      return;
    }

    try {
      setIsUploading(true);
      
      if (uploadMethod === 'file' && uploadFile) {
        await documentsAPI.upload(uploadFile, {
          name: documentName || uploadFile.name,
          description: documentDescription || undefined
        });
      } else if (uploadMethod === 'url') {
        await documentsAPI.createFromUrl({
          url,
          name: documentName || `Website: ${url}`,
          description: documentDescription || `Content from ${url}`
        });
      }
      
      toast({
        title: "Document processed",
        description: "Your data source has been added and processing has started.",
      });
      
      // Reset form
      setUploadFile(null);
      setUrl('');
      setDocumentName('');
      setDocumentDescription('');
      setUploadMethod(null);
      setIsUploadDialogOpen(false);
      
      // Refresh document list
      fetchDocuments();
      
    } catch (err) {
      console.error('Upload error:', err);
      toast({
        title: "Upload failed",
        description: err instanceof Error ? err.message : "An unknown error occurred",
        variant: "destructive"
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (documentId: string) => {
    try {
      setIsDeleting(true);
      await documentsAPI.delete(documentId);
      
      // Remove the document from the list
      setDocuments(prev => prev.filter(doc => doc.id !== documentId));
      setDeleteConfirmId(null);
      
      toast({
        title: "Success",
        description: "Document deleted successfully",
      });
    } catch (error) {
      console.error('Error deleting document:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to delete document",
        variant: "destructive"
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown size';
    
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  };

  const handleWebsiteSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    try {
      setIsUploading(true);
      const response = await documentsAPI.createFromUrl({
        url,
        name: documentName || undefined,
        description: documentDescription || undefined
      });

      // Add the new document to the list
      setDocuments(prev => [...prev, response]);
      setUrl('');
      setDocumentName('');
      setDocumentDescription('');
      setUploadMethod(null);
      setIsUploadDialogOpen(false);
      toast({
        title: "Success",
        description: "Website content has been added to your data sources",
      });
    } catch (error) {
      console.error('Error adding website:', error);
      toast({
        title: "Error",
        description: "Failed to add website content. Please check the URL and try again.",
        variant: "destructive"
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <TooltipProvider>
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Data Sources</h1>
          <Dialog open={isUploadDialogOpen} onOpenChange={setIsUploadDialogOpen}>
            <DialogTrigger asChild>
              <Button className="inline-flex items-center">
                <PlusIcon className="w-5 h-5 mr-2" />
                Add New Data Source
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Data Source</DialogTitle>
                <DialogDescription>
                  Choose how you want to add data to your knowledge base.
                </DialogDescription>
              </DialogHeader>

              <form onSubmit={handleUpload} className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <Button
                    type="button"
                    variant={uploadMethod === 'file' ? 'default' : 'outline'}
                    className="w-full h-24 flex flex-col items-center justify-center space-y-2"
                    onClick={() => setUploadMethod('file')}
                  >
                    <DocumentTextIcon className="w-6 h-6" />
                    <span>Upload File</span>
                  </Button>
                  <Button
                    type="button"
                    variant={uploadMethod === 'url' ? 'default' : 'outline'}
                    className="w-full h-24 flex flex-col items-center justify-center space-y-2"
                    onClick={() => setUploadMethod('url')}
                  >
                    <GlobeAltIcon className="w-6 h-6" />
                    <span>Website URL</span>
                  </Button>
                </div>

                {uploadMethod === 'file' && (
                  <div className="space-y-4">
                    <div className="grid gap-2">
                      <Label htmlFor="file">File</Label>
                      <Input 
                        id="file" 
                        type="file" 
                        onChange={handleFileChange}
                        accept=".pdf,.txt,.docx"
                        required
                      />
                      <p className="text-sm text-muted-foreground">
                        Supported formats: PDF, TXT, DOCX
                      </p>
                    </div>
                  </div>
                )}

                {uploadMethod === 'url' && (
                  <div className="space-y-4">
                    <div className="grid gap-2">
                      <Label htmlFor="url">Website URL</Label>
                      <Input 
                        id="url" 
                        type="url" 
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="https://example.com"
                        required
                      />
                    </div>
                  </div>
                )}

                {(uploadMethod === 'file' || uploadMethod === 'url') && (
                  <>
                    <div className="grid gap-2">
                      <Label htmlFor="name">Name</Label>
                      <Input 
                        id="name" 
                        value={documentName} 
                        onChange={(e) => setDocumentName(e.target.value)}
                        placeholder="Document name"
                        required
                      />
                    </div>
                    <div className="grid gap-2">
                      <Label htmlFor="description">Description (optional)</Label>
                      <Textarea 
                        id="description" 
                        value={documentDescription} 
                        onChange={(e) => setDocumentDescription(e.target.value)}
                        placeholder="Brief description of this document"
                        rows={3}
                      />
                    </div>
                  </>
                )}

                <DialogFooter>
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={() => {
                      setIsUploadDialogOpen(false);
                      setUploadMethod(null);
                      setUploadFile(null);
                      setUrl('');
                      setDocumentName('');
                      setDocumentDescription('');
                    }}
                    disabled={isUploading}
                  >
                    Cancel
                  </Button>
                  <Button 
                    type="submit" 
                    disabled={isUploading || (uploadMethod === 'file' && !uploadFile) || (uploadMethod === 'url' && !url)}
                  >
                    {isUploading ? 'Processing...' : 'Add Data Source'}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto"></div>
            <p className="mt-4 text-muted-foreground">Loading your data sources...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12 bg-destructive/10 rounded-lg">
            <p className="text-destructive">{error}</p>
            <Button 
              onClick={() => fetchDocuments()}
              className="mt-4"
            >
              Retry
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {documents.map((doc) => (
              <Card key={doc.id} className="overflow-hidden">
                <CardHeader className="pb-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">{doc.name}</CardTitle>
                      <CardDescription className="mt-1">
                        {doc.metadata?.type && typeof doc.metadata.type === 'string' ? doc.metadata.type.toUpperCase() : 'DOCUMENT'} • {new Date(doc.createdAt).toLocaleDateString()}
                      </CardDescription>
                    </div>
                    <Dialog open={deleteConfirmId === doc.id} onOpenChange={(open) => !open && setDeleteConfirmId(null)}>
                      <DialogTrigger asChild>
                        <Button 
                          variant="ghost" 
                          size="icon"
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteConfirmId(doc.id);
                          }}
                        >
                          <TrashIcon className="h-5 w-5 text-destructive" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Delete Document</DialogTitle>
                          <DialogDescription>
                            Are you sure you want to delete "{doc.name}"? This action cannot be undone.
                          </DialogDescription>
                        </DialogHeader>
                        <DialogFooter className="mt-4">
                          <Button 
                            variant="outline" 
                            onClick={() => setDeleteConfirmId(null)}
                          >
                            Cancel
                          </Button>
                          <Button 
                            variant="destructive"
                            onClick={() => handleDelete(doc.id)}
                          >
                            Delete
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <DocumentStatusBadge status={doc.processingStatus} error={doc.error} />
                    {doc.processingStatus === 'processing' && (
                      <Progress value={-1} className="animate-pulse" />
                    )}
                    {doc.processingStatus === 'completed' && (
                      <div className="text-sm text-gray-500">
                        {doc.chunkCount} chunks created
                      </div>
                    )}
                    {doc.processingStats && doc.processingStatus === 'completed' && (
                      <ProcessingStats stats={doc.processingStats} />
                    )}
                    <p className="text-sm text-gray-500">
                      {doc.metadata?.description || 'No description provided'}
                    </p>
                  </div>
                  <div className="mt-4 flex items-center gap-4 text-xs text-muted-foreground">
                    {doc.metadata?.source_url && (
                      <div className="flex items-center">
                        <GlobeAltIcon className="w-4 h-4 mr-1" />
                        <a 
                          href={doc.metadata.source_url as string} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="hover:underline truncate max-w-[200px]"
                        >
                          {doc.metadata.source_url as string}
                        </a>
                      </div>
                    )}
                    {doc.metadata?.word_count && (
                      <div className="flex items-center">
                        <DocumentTextIcon className="w-4 h-4 mr-1" />
                        <span>{doc.metadata.word_count} words</span>
                      </div>
                    )}
                  </div>
                </CardContent>
                <CardFooter className="border-t pt-3 text-xs text-muted-foreground">
                  <div className="w-full grid grid-cols-2 gap-2">
                    {doc.metadata?.fileSize && (
                      <div>Size: {formatFileSize(doc.metadata.fileSize as number)}</div>
                    )}
                    {doc.metadata?.pageCount && (
                      <div>Pages: {doc.metadata.pageCount as number}</div>
                    )}
                    {doc.metadata?.wordCount && (
                      <div>Words: {(doc.metadata.wordCount as number).toLocaleString()}</div>
                    )}
                  </div>
                </CardFooter>
              </Card>
            ))}

            {documents.length === 0 && (
              <div className="col-span-full">
                <Card className="border-dashed">
                  <CardContent className="pt-6 text-center">
                    <DocumentTextIcon className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                    <h3 className="text-lg font-medium mb-2">No data sources yet</h3>
                    <p className="text-muted-foreground mb-4">
                      Upload documents to create knowledge bases for your chatbots
                    </p>
                    <Button 
                      onClick={() => setIsUploadDialogOpen(true)}
                      className="mt-2"
                    >
                      <PlusIcon className="w-5 h-5 mr-2" />
                      Upload Your First Document
                    </Button>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        )}
      </div>
    </TooltipProvider>
  );
} 