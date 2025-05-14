'use client';

import { useEffect, useState } from 'react';
import { getDocuments, deleteDocument } from '@/lib/api';
import type { Document } from '@/types/api';

export default function DocumentList() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getDocuments();
      setDocuments(data);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: string } } };
      setError(error.response?.data?.error || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (documentId: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      await deleteDocument(documentId);
      setDocuments(documents.filter(doc => doc.id !== documentId));
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: string } } };
      setError(error.response?.data?.error || 'Failed to delete document');
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  if (loading) {
    return <div className="text-center py-4">Loading documents...</div>;
  }

  if (error) {
    return (
      <div className="text-center py-4 text-red-600">
        {error}
        <button
          onClick={loadDocuments}
          className="ml-2 text-blue-600 hover:text-blue-800"
        >
          Retry
        </button>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-4 text-gray-500">
        No documents uploaded yet
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {documents.map((doc) => (
        <div
          key={doc.id}
          className="border rounded-lg p-4 flex items-center justify-between"
        >
          <div>
            <h3 className="font-medium">{doc.name}</h3>
            <div className="text-sm text-gray-500">
              Status: {doc.processingStatus}
              {doc.chunkCount !== undefined && (
                <span className="ml-2">Chunks: {doc.chunkCount}</span>
              )}
            </div>
            {doc.error && (
              <div className="text-sm text-red-600 mt-1">{doc.error}</div>
            )}
          </div>
          <button
            onClick={() => handleDelete(doc.id)}
            className="text-red-600 hover:text-red-800"
          >
            Delete
          </button>
        </div>
      ))}
    </div>
  );
}