import { HomeIcon, ChatBubbleLeftRightIcon, DocumentTextIcon, LinkIcon, Cog6ToothIcon, BookOpenIcon } from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Chatbots', href: '/dashboard/chatbots', icon: ChatBubbleLeftRightIcon },
  { name: 'Data Sources', href: '/dashboard/datasources', icon: DocumentTextIcon },
  { name: 'Integrations', href: '/dashboard/integrations', icon: LinkIcon },
  { name: 'Settings', href: '/dashboard/settings', icon: Cog6ToothIcon },
  { name: 'Testing Guide', href: '/dashboard/guide', icon: BookOpenIcon },
]; 