'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { 
  DocumentTextIcon, 
  GlobeAltIcon, 
  QuestionMarkCircleIcon,
  ArrowUpTrayIcon,
  PlusIcon,
  XMarkIcon,
  ArchiveBoxIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import ChatbotConfig from '@/components/chatbot/ChatbotConfig';
import { ChatbotSettings } from '@/types/chatbot';
import { Toaster, toast } from 'react-hot-toast';
import { documentsAPI } from '@/lib/api';

const MAX_CHARS = 200000;

interface QAPair {
  id: string;
  question: string;
  answer: string;
}

interface UploadedDocument {
  id: string;
  contentLength: number;
}

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
  type?: string;
  description?: string;
}

export default function NewChatbotPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [uploadedDocument, setUploadedDocument] = useState<UploadedDocument | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadMethod, setUploadMethod] = useState<'file' | 'url' | 'qa' | 'existing' | null>(null);
  const [url, setUrl] = useState('');
  const [qaPairs, setQaPairs] = useState<QAPair[]>([]);
  const [savedPairs, setSavedPairs] = useState<Set<string>>(new Set());
  const [settings, setSettings] = useState<ChatbotSettings>({
    temperature: 0.7,
    maxTokens: 1024,
    model: "llama3-70b-8192",
    instructions: ""
  });
  const [existingDocuments, setExistingDocuments] = useState<Document[]>([]);
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);

  useEffect(() => {
    if (uploadMethod === 'existing') {
      fetchExistingDocuments();
    }
  }, [uploadMethod]);

  const fetchExistingDocuments = async () => {
    try {
      setLoadingDocuments(true);
      const docs = await documentsAPI.list();
      setExistingDocuments(docs.filter(doc => 
        doc.processingStatus === 'completed' || 
        doc.processingStatus === 'processing' || 
        doc.processingStatus === 'pending'
      ));
    } catch (error) {
      console.error('Error fetching documents:', error);
      toast.error('Failed to load existing data sources');
    } finally {
      setLoadingDocuments(false);
    }
  };

  const handleDocumentSelection = (documentId: string) => {
    setSelectedDocuments(prev => {
      if (prev.includes(documentId)) {
        return prev.filter(id => id !== documentId);
      } else {
        return [...prev, documentId];
      }
    });
  };

  const handleUseSelectedDocuments = () => {
    if (selectedDocuments.length === 0) {
      toast.error('Please select at least one document');
      return;
    }

    const primaryDoc = existingDocuments.find(doc => doc.id === selectedDocuments[0]);
    if (primaryDoc) {
      setUploadedDocument({
        id: primaryDoc.id,
        contentLength: primaryDoc.metadata?.fileSize || 0
      });
    }
  };

  const getTotalQACharacters = () => {
    return qaPairs.reduce((total, pair) => total + pair.question.length + pair.answer.length, 0);
  };

  const getCharacterCount = () => {
    if (uploadedDocument) {
      return Math.floor(uploadedDocument.contentLength / 2);
    }
    return getTotalQACharacters();
  };

  const characterCount = getCharacterCount();
  const progress = (characterCount / MAX_CHARS) * 100;

  const handleAddQAPair = () => {
    setQaPairs([...qaPairs, { id: Date.now().toString(), question: '', answer: '' }]);
  };

  const handleSaveQAPair = (id: string) => {
    if (!qaPairs.find(pair => pair.id === id)?.question || !qaPairs.find(pair => pair.id === id)?.answer) {
      alert('Please fill both question and answer before saving');
      return;
    }
    setSavedPairs(prev => new Set([...prev, id]));
  };

  const handleQAPairChange = (id: string, field: 'question' | 'answer', value: string) => {
    if (savedPairs.has(id)) {
      setSavedPairs(prev => {
        const newSet = new Set(prev);
        newSet.delete(id);
        return newSet;
      });
    }

    const newPairs = qaPairs.map(pair => {
      if (pair.id === id) {
        return { ...pair, [field]: value };
      }
      return pair;
    });
    setQaPairs(newPairs);

    const formattedQA = newPairs
      .filter(pair => savedPairs.has(pair.id))
      .map(pair => `Q: ${pair.question}\nA: ${pair.answer}`)
      .join('\n\n');
    
    setUploadedDocument({
      id: 'qa-' + Date.now(),
      contentLength: formattedQA.length
    });
  };

  const handleRemoveQAPair = (id: string) => {
    const newPairs = qaPairs.filter(pair => pair.id !== id);
    setQaPairs(newPairs);

    const formattedQA = newPairs
      .filter(pair => savedPairs.has(pair.id))
      .map(pair => `Q: ${pair.question}\nA: ${pair.answer}`)
      .join('\n\n');
    
    setUploadedDocument({
      id: 'qa-' + Date.now(),
      contentLength: formattedQA.length
    });
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    try {
        console.log('Starting file upload:', { 
            fileName: file.name, 
            fileType: file.type, 
            fileSize: file.size,
            lastModified: new Date(file.lastModified).toISOString()
        });
        
        const token = localStorage.getItem('auth_token');
        if (!token) {
            throw new Error('No authentication token found. Please log in again.');
        }
        console.log('Authentication token retrieved:', token.substring(0, 10) + '...');

        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', file.name);
        formData.append('description', 'Uploaded from device');

        console.log('Preparing to send request to backend...');
        
        try {
            const testResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8080'}/health`, {
                method: 'GET',
                mode: 'cors',
            });
            console.log('Backend health check response:', testResponse.status);
        } catch (error) {
            console.error('Backend connectivity test failed:', error);
            throw new Error('Cannot connect to backend server. Please ensure the server is running.');
        }
        
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8080'}/api/documents/upload`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Accept': 'application/json',
            },
            credentials: 'include',
            mode: 'cors',
            body: formData,
        });

        console.log('Response received:', {
            status: response.status,
            statusText: response.statusText,
            headers: Object.fromEntries(response.headers.entries())
        });

        if (!response.ok) {
            let errorMessage = `Upload failed: ${response.status} ${response.statusText}`;
            try {
                const errorData = await response.json();
                errorMessage = errorData.detail || errorMessage;
                console.error('Error response:', errorData);
            } catch (e) {
                console.error('Could not parse error response:', e);
            }
            throw new Error(errorMessage);
        }

        const data = await response.json();
        console.log('Upload successful:', data);
        
        setUploadedDocument({
            id: data.id,
            contentLength: data.fileSize || 0
        });
        
        alert('File uploaded successfully!');
        
    } catch (error) {
        console.error('Error uploading file:', error);
        alert(error instanceof Error ? error.message : 'Error uploading file. Please try again.');
    } finally {
        setIsLoading(false);
    }
  };

  const handleUrlSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setIsLoading(true);
    try {
        const token = localStorage.getItem('auth_token');
        if (!token) {
            throw new Error('No authentication token found. Please log in again.');
        }

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8080'}/api/documents/url`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({
                url,
                name: `Website: ${url}`,
                description: `Content scraped from ${url}`
            }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to process URL');
        }

        const data = await response.json();
        setUploadedDocument({
            id: data.id,
            contentLength: data.metadata.word_count * 6 // Approximate characters from word count
        });

        toast.success('Website content processed successfully!');
    } catch (error) {
        console.error('Error processing URL:', error);
        toast.error(error instanceof Error ? error.message : 'Error processing URL. Please try again.');
    } finally {
        setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (currentStep === 1 && (uploadedDocument || (uploadMethod === 'existing' && selectedDocuments.length > 0))) {
      setCurrentStep(2);
    } else if (currentStep === 2) {
      try {
        setIsLoading(true);
        
        const token = localStorage.getItem('auth_token');
        if (!token) {
          throw new Error('No authentication token found. Please log in again.');
        }

        let documentIds: string[] = [];
        if (uploadMethod === 'existing') {
          documentIds = selectedDocuments;
        } else if (uploadedDocument) {
          documentIds = [uploadedDocument.id];
        }

        console.log('Creating chatbot with settings:', {
          name,
          description,
          settings,
          documents: documentIds
        });

        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8080'}/api/chatbots`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            name,
            description,
            settings,
            documents: documentIds,
          }),
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error('Server error response:', errorText);
          throw new Error(`Failed to create chatbot: ${response.status} ${errorText}`);
        }

        const data = await response.json();
        console.log('Chatbot created successfully:', data);
        
        toast.success('Chatbot created successfully!', {
          duration: 3000
        });
        
        setTimeout(() => {
          router.push(`/dashboard/chatbots/${data.id}/config`);
        }, 3000);
      } catch (error) {
        console.error('Error creating chatbot:', error);
        toast.error('Failed to create chatbot: ' + (error instanceof Error ? error.message : 'Unknown error'));
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleContinue = () => {
    if (currentStep === 1) {
      setCurrentStep(2);
    } else {
      handleSubmit({ preventDefault: () => {} } as React.FormEvent<HTMLFormElement>);
    }
  };

  const uploadMethods = [
    {
      id: 'file',
      name: 'Upload Files',
      description: 'Upload DOCX or TXT files',
      icon: DocumentTextIcon,
    },
    {
      id: 'url',
      name: 'Website URL',
      description: 'Scrape content from a website',
      icon: GlobeAltIcon,
    },
    {
      id: 'qa',
      name: 'Q&A Pairs',
      description: 'Add question and answer pairs',
      icon: QuestionMarkCircleIcon,
    },
    {
      id: 'existing',
      name: 'Existing Data Sources',
      description: 'Use your existing data sources',
      icon: ArchiveBoxIcon,
    },
  ];

  const handleNameChange = (newName: string) => {
    setName(newName);
  };

  const handleDescriptionChange = (newDescription: string) => {
    setDescription(newDescription);
  };

  return (
    <div className="min-h-screen bg-background">
      <Toaster position="top-center" />
      <div className="max-w-7xl mx-auto p-6">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-foreground">Create a New Chatbot</h1>
          {currentStep === 2 && (
            <button
              type="button"
              onClick={() => setCurrentStep(1)}
              className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors"
            >
              ← Back to Knowledge Base
            </button>
          )}
        </div>

        {currentStep === 1 ? (
          <div className="space-y-6">
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              {uploadMethods.map((method) => (
                <button
                  key={method.id}
                  onClick={() => setUploadMethod(method.id as 'file' | 'url' | 'qa' | 'existing')}
                  className={`relative flex flex-col items-center p-6 border rounded-lg transition-all ${
                    uploadMethod === method.id
                      ? 'border-primary bg-primary/5 ring-2 ring-primary/20'
                      : 'border-border hover:border-primary/50 hover:bg-primary/5'
                  }`}
                >
                  <method.icon className="h-8 w-8 text-primary" />
                  <h3 className="mt-4 font-semibold text-foreground">{method.name}</h3>
                  <p className="mt-1 text-sm text-muted-foreground text-center">
                    {method.description}
                  </p>
                </button>
              ))}
            </div>

            {uploadMethod === 'file' && (
              <div className="mt-6 p-6 border border-border rounded-lg bg-card">
                <label className="block text-sm font-medium mb-2 text-foreground">Upload Files</label>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={handleFileUpload}
                  className="block w-full text-sm text-foreground file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
                />
                {isLoading && (
                  <div className="mt-4 text-sm text-muted-foreground">
                    Uploading file...
                  </div>
                )}
              </div>
            )}

            {uploadMethod === 'url' && (
              <div className="mt-6 p-6 border border-border rounded-lg bg-card">
                <form onSubmit={handleUrlSubmit} className="space-y-4">
                  <div>
                    <label htmlFor="url" className="block text-sm font-medium mb-2 text-foreground">Website URL</label>
                    <input
                      type="url"
                      id="url"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="https://example.com"
                      required
                      className="block w-full rounded-md border-border bg-input px-3 py-2 text-foreground shadow-sm focus:ring-2 focus:ring-primary focus:border-primary sm:text-sm"
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="inline-flex justify-center rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? 'Processing...' : 'Fetch Content'}
                  </button>
                </form>
              </div>
            )}

            {uploadMethod === 'qa' && (
              <div className="mt-6 space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-medium text-foreground">Questions & Answers</h3>
                  <button
                    type="button"
                    onClick={handleAddQAPair}
                    disabled={getTotalQACharacters() >= MAX_CHARS}
                    className="inline-flex items-center px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <PlusIcon className="h-5 w-5 mr-2" />
                    Add Q&A Pair
                  </button>
                </div>

                {qaPairs.map((pair) => (
                  <div key={pair.id} className="space-y-4 p-4 border border-border rounded-lg bg-card">
                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">Question</label>
                      <div className="flex gap-4">
                        <input
                          type="text"
                          value={pair.question}
                          onChange={(e) => handleQAPairChange(pair.id, 'question', e.target.value)}
                          placeholder="Enter your question"
                          disabled={savedPairs.has(pair.id)}
                          className="flex-1 rounded-md border-border bg-input px-3 py-2 text-foreground shadow-sm focus:ring-2 focus:ring-primary focus:border-primary sm:text-sm disabled:opacity-50"
                        />
                        <button
                          type="button"
                          onClick={() => handleRemoveQAPair(pair.id)}
                          className="p-2 text-destructive hover:text-destructive/70"
                        >
                          <XMarkIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-2 text-foreground">Answer</label>
                      <textarea
                        value={pair.answer}
                        onChange={(e) => handleQAPairChange(pair.id, 'answer', e.target.value)}
                        placeholder="Enter your answer"
                        rows={3}
                        disabled={savedPairs.has(pair.id)}
                        className="w-full rounded-md border-border bg-input px-3 py-2 text-foreground shadow-sm focus:ring-2 focus:ring-primary focus:border-primary sm:text-sm disabled:opacity-50"
                      />
                    </div>
                    <div className="flex justify-end mt-2">
                      {!savedPairs.has(pair.id) ? (
                        <button
                          type="button"
                          onClick={() => handleSaveQAPair(pair.id)}
                          className="inline-flex items-center px-4 py-2 rounded-md bg-green-600 text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                        >
                          Save
                        </button>
                      ) : (
                        <span className="inline-flex items-center px-4 py-2 text-sm text-green-600">
                          <svg className="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                          Saved
                        </span>
                      )}
                    </div>
                  </div>
                ))}

                {qaPairs.length > 0 && (
                  <div className="mt-4 p-4 border border-border rounded-lg bg-card">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-foreground">Total Characters</span>
                      <span className="text-sm text-muted-foreground">
                        {getTotalQACharacters().toLocaleString()} / {MAX_CHARS.toLocaleString()}
                      </span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div
                        className="bg-primary rounded-full h-2 transition-all"
                        style={{ width: `${Math.min((getTotalQACharacters() / MAX_CHARS) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            )}

            {uploadMethod === 'existing' && (
              <div className="mt-6 space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-medium text-foreground">Select Data Sources</h3>
                </div>
                
                {loadingDocuments ? (
                  <div className="text-center py-8">
                    <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto"></div>
                    <p className="mt-4 text-muted-foreground">Loading your data sources...</p>
                  </div>
                ) : existingDocuments.length === 0 ? (
                  <div className="text-center py-8 border border-dashed rounded-lg">
                    <DocumentTextIcon className="h-12 w-12 mx-auto text-muted-foreground" />
                    <p className="mt-2 text-muted-foreground">You don't have any data sources yet</p>
                    <button
                      type="button"
                      onClick={() => setUploadMethod('file')}
                      className="mt-4 inline-flex items-center px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
                    >
                      <PlusIcon className="h-5 w-5 mr-2" />
                      Upload a Document First
                    </button>
                  </div>
                ) : (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {existingDocuments.map((doc) => (
                        <div 
                          key={doc.id}
                          onClick={() => handleDocumentSelection(doc.id)}
                          className={`p-4 border rounded-lg cursor-pointer transition-all ${
                            selectedDocuments.includes(doc.id) 
                              ? 'border-primary bg-primary/5 ring-2 ring-primary/20' 
                              : 'border-border hover:border-primary/50'
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h4 className="font-medium text-foreground">{doc.name}</h4>
                              <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                                {doc.description || 'No description'}
                              </p>
                              <div className="flex items-center mt-2 text-xs text-muted-foreground">
                                <span className="capitalize">{doc.type}</span>
                                <span className="mx-2">•</span>
                                <span>{new Date(doc.createdAt).toLocaleDateString()}</span>
                                {doc.metadata?.fileSize && (
                                  <>
                                    <span className="mx-2">•</span>
                                    <span>{(doc.metadata.fileSize / 1024).toFixed(1)} KB</span>
                                  </>
                                )}
                                <span className="mx-2">•</span>
                                <div className={`inline-flex items-center ${
                                  doc.processingStatus === 'completed' ? 'text-green-500' :
                                  doc.processingStatus === 'failed' ? 'text-red-500' :
                                  'text-yellow-500'
                                }`}>
                                  <div className="w-2 h-2 rounded-full mr-1" style={{
                                    backgroundColor: doc.processingStatus === 'completed' ? '#22c55e' :
                                                  doc.processingStatus === 'failed' ? '#ef4444' :
                                                  '#eab308'
                                  }}></div>
                                  <span className="capitalize">{doc.processingStatus}</span>
                                </div>
                              </div>
                            </div>
                            <div className="ml-4">
                              {selectedDocuments.includes(doc.id) && (
                                <CheckCircleIcon className="h-6 w-6 text-primary" />
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    <div className="mt-6 flex justify-end">
                      <button
                        type="button"
                        onClick={handleUseSelectedDocuments}
                        disabled={selectedDocuments.length === 0}
                        className="inline-flex items-center px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        Use Selected Data Sources ({selectedDocuments.length})
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}

            {(uploadMethod === 'file' || uploadMethod === 'url') && uploadedDocument && (
              <div className="mt-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-foreground">Knowledge Base Size</span>
                  <span className="text-sm text-muted-foreground">
                    {characterCount.toLocaleString()} / {MAX_CHARS.toLocaleString()} characters
                    {uploadMethod === 'file' && (
                      <span className="ml-2 text-xs">
                        (File size: {(uploadedDocument.contentLength / 1024).toFixed(2)} KB)
                      </span>
                    )}
                  </span>
                </div>
                <div className="w-full bg-muted rounded-full h-2">
                  <div
                    className="bg-primary rounded-full h-2 transition-all"
                    style={{ width: `${Math.min(progress, 100)}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        ) : (
          <ChatbotConfig
            name={name}
            description={description}
            documents={uploadedDocument ? [uploadedDocument.id] : []}
            onNameChange={handleNameChange}
            onDescriptionChange={handleDescriptionChange}
            onSettingsChange={setSettings}
            onSubmit={() => handleSubmit({ preventDefault: () => {} } as React.FormEvent<HTMLFormElement>)}
          />
        )}

        {currentStep === 1 && (
          <div className="mt-8 flex justify-end">
            <button
              onClick={handleContinue}
              disabled={isLoading || (!uploadedDocument && !(uploadMethod === 'existing' && selectedDocuments.length > 0))}
              className="inline-flex justify-center rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Processing...' : 'Continue to Configuration'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}