'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
  ChatBubbleLeftRightIcon,
  UserGroupIcon,
  DocumentIcon,
  PlusIcon,
} from '@heroicons/react/24/outline'

interface DashboardStats {
  total_chatbots: number;
  total_conversations: number;
  total_datasources: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    total_chatbots: 0,
    total_conversations: 0,
    total_datasources: 0
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setIsLoading(true);
        const token = localStorage.getItem('auth_token');
        if (!token) {
          throw new Error('No auth token found');
        }

        // Fetch stats from the API
        const response = await fetch('http://localhost:8000/api/diagnostics/stats/overview', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to fetch stats');
        }

        const data = await response.json();
        setStats({
          total_chatbots: data.total_chatbots || 0,
          total_conversations: data.total_conversations || 0,
          total_datasources: data.total_datasources || 0
        });
      } catch (err) {
        console.error('Error fetching stats:', err);
        const errorMessage = err instanceof Error ? err.message : 'Failed to load stats';
        setError(errorMessage);
        // Set default values on error
        setStats({
          total_chatbots: 0,
          total_conversations: 0,
          total_datasources: 0
        });
        // Show error in UI if needed
        if (errorMessage.includes('Could not validate credentials')) {
          // Handle authentication error
          setError('Please sign in again to view your statistics');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, []);

  const statsDisplay = [
    { 
      name: 'Total Chatbots', 
      value: isLoading ? '-' : stats.total_chatbots.toString(), 
      icon: ChatBubbleLeftRightIcon 
    },
    { 
      name: 'Total Conversations', 
      value: isLoading ? '-' : stats.total_conversations.toString(), 
      icon: UserGroupIcon 
    },
    { 
      name: 'Total Data Sources', 
      value: isLoading ? '-' : stats.total_datasources.toString(), 
      icon: DocumentIcon 
    },
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            Welcome to your Dashboard!
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Here's what's happening with your chatbots today.
          </p>
        </div>
        <Link
          href="/dashboard/chatbots/new"
          className="inline-flex items-center gap-x-2 rounded-full bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
        >
          <PlusIcon className="-ml-0.5 h-5 w-5" aria-hidden="true" />
          New Chatbot
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {statsDisplay.map((stat, index) => (
          <motion.div
            key={stat.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: index * 0.1 }}
            className="relative overflow-hidden rounded-lg border border-border bg-muted/50 backdrop-blur-xl px-6 py-5 shadow"
          >
            <dt>
              <div className="absolute rounded-md bg-primary/10 p-3">
                <stat.icon className="h-6 w-6 text-primary" aria-hidden="true" />
              </div>
              <p className="ml-16 truncate text-sm font-medium text-muted-foreground">
                {stat.name}
              </p>
            </dt>
            <dd className="ml-16 flex items-baseline">
              <p className="text-2xl font-semibold text-foreground">
                {isLoading ? (
                  <span className="animate-pulse">...</span>
                ) : (
                  stat.value
                )}
              </p>
            </dd>
          </motion.div>
        ))}
      </div>

      {/* Quick start guide */}
      <div className="rounded-lg border border-border bg-muted/50 backdrop-blur-xl p-6">
        <h2 className="text-base font-semibold text-foreground">
          Quick Start Guide
        </h2>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="relative rounded-lg border border-border bg-background p-4">
            <dt className="flex items-center gap-x-3 text-sm font-semibold text-foreground">
              Create a Chatbot
            </dt>
            <dd className="mt-2 text-sm text-muted-foreground">
              Start by creating your first AI-powered chatbot with custom knowledge base.
            </dd>
          </div>
          <div className="relative rounded-lg border border-border bg-background p-4">
            <dt className="flex items-center gap-x-3 text-sm font-semibold text-foreground">
              Train Your Bot
            </dt>
            <dd className="mt-2 text-sm text-muted-foreground">
              Upload documents or provide information to train your chatbot.
            </dd>
          </div>
          <div className="relative rounded-lg border border-border bg-background p-4">
            <dt className="flex items-center gap-x-3 text-sm font-semibold text-foreground">
              Customize
            </dt>
            <dd className="mt-2 text-sm text-muted-foreground">
              Personalize your chatbot's appearance and behavior.
            </dd>
          </div>
          <div className="relative rounded-lg border border-border bg-background p-4">
            <dt className="flex items-center gap-x-3 text-sm font-semibold text-foreground">
              Deploy
            </dt>
            <dd className="mt-2 text-sm text-muted-foreground">
              Integrate your chatbot into your website or preferred platform.
            </dd>
          </div>
        </div>
      </div>
    </div>
  )
} 