'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { createChatbot, getDocuments } from '@/lib/api';
import type { Document } from '@/types/api';

interface ApiError {
  response?: {
    data?: {
      error?: string;
    };
  };
  message: string;
}

export default function ChatbotForm() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);
  const [temperature, setTemperature] = useState(0.7);
  const [instructions, setInstructions] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const data = await getDocuments();
      setDocuments(data);
    } catch (err: unknown) {
      const error = err as ApiError;
      setError(error.response?.data?.error || 'Failed to load documents');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name) return;

    try {
      setLoading(true);
      setError('');

      await createChatbot({
        name,
        description,
        documents: selectedDocuments,
        settings: {
          temperature,
          instructions: instructions || undefined,
        },
      });

      router.push('/dashboard/chatbots');
      router.refresh();
    } catch (err: unknown) {
      const error = err as ApiError;
      setError(error.response?.data?.error || 'Failed to create chatbot');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700">
          Chatbot Name
        </label>
        <input
          type="text"
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
            focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          disabled={loading}
          required
        />
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700">
          Description (Optional)
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
            focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          disabled={loading}
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Knowledge Base Documents
        </label>
        <div className="space-y-2 max-h-48 overflow-y-auto border rounded-md p-2">
          {documents.map((doc) => (
            <label key={doc.id} className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={selectedDocuments.includes(doc.id)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedDocuments([...selectedDocuments, doc.id]);
                  } else {
                    setSelectedDocuments(selectedDocuments.filter(id => id !== doc.id));
                  }
                }}
                className="rounded border-gray-300 text-blue-600
                  focus:ring-blue-500"
                disabled={loading || doc.processingStatus !== 'completed'}
              />
              <span className="text-sm">
                {doc.name}
                {doc.processingStatus !== 'completed' && (
                  <span className="ml-2 text-yellow-600 text-xs">
                    ({doc.processingStatus})
                  </span>
                )}
              </span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label htmlFor="temperature" className="block text-sm font-medium text-gray-700">
          Temperature ({temperature})
        </label>
        <input
          type="range"
          id="temperature"
          min="0"
          max="1"
          step="0.1"
          value={temperature}
          onChange={(e) => setTemperature(parseFloat(e.target.value))}
          className="mt-1 block w-full"
          disabled={loading}
        />
      </div>

      <div>
        <label htmlFor="instructions" className="block text-sm font-medium text-gray-700">
          System Instructions (Optional)
        </label>
        <textarea
          id="instructions"
          value={instructions}
          onChange={(e) => setInstructions(e.target.value)}
          rows={4}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm
            focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          disabled={loading}
          placeholder="Enter any specific instructions for the chatbot..."
        />
      </div>

      {error && (
        <div className="text-sm text-red-600">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={!name || loading}
        className="w-full inline-flex justify-center rounded-md border border-transparent
          bg-blue-600 py-2 px-4 text-sm font-medium text-white shadow-sm
          hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500
          focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Creating...' : 'Create Chatbot'}
      </button>
    </form>
  );
}