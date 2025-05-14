# Frontend Context Documentation

## Overview
This document provides a comprehensive overview of the frontend codebase for the ChatSphere platform. The frontend is built using Next.js with TypeScript and follows the App Router pattern. It includes authentication via Supabase, UI components styled with Tailwind CSS, and animations using Framer Motion.

## Directory Structure

### Root Configuration Files

- **next.config.ts**: Next.js configuration file that defines build-time options for the application.
- **tsconfig.json**: TypeScript configuration that sets compiler options, including path aliases for imports (e.g., `@/*` for `./src/*`).
- **tailwind.config.ts**: Tailwind CSS configuration for styling the application, likely including custom theme settings.
- **postcss.config.mjs**: PostCSS configuration used by Tailwind CSS for processing styles.
- **eslint.config.mjs**: ESLint configuration for code linting and maintaining code quality.
- **package.json**: Defines project dependencies and scripts, including development commands using Turbopack for faster builds.

### Source Code (`src/`)

#### App Directory (`src/app/`)
Implements Next.js App Router pattern for routing and page layouts:

- **layout.tsx**: Root layout component that wraps all pages, includes the `AuthProvider` context and sets up the base HTML structure with the Inter font and dark mode by default.
- **page.tsx**: Homepage component that renders the `Navigation` and `Hero` components.
- **globals.css**: Global CSS styles for the application.
- **favicon.ico**: Application favicon.

##### Authentication Pages
- **login/page.tsx**: Login page for user authentication.
- **register/page.tsx**: Registration page for new users.

##### Dashboard Section
- **dashboard/layout.tsx**: Layout component specific to the dashboard section.
- **dashboard/page.tsx**: Main dashboard page that displays user statistics (chatbots, conversations, response rate) and provides a link to create new chatbots. Uses Framer Motion for animations and Heroicons for icons.
- **dashboard/chatbots/**: Directory for chatbot management pages.

##### API Routes
- **api/auth/**: Authentication API endpoints.
- **api/chat/**: Chat functionality API endpoints.
- **api/chatbots/**: Chatbot management API endpoints.
- **api/notion/**: Notion integration API endpoints.
- **api/register/**: User registration API endpoints.

#### Components (`src/components/`)

- **navigation.tsx**: Navigation component that implements a responsive header with mobile menu support using Headless UI. Includes the ChatSphere logo and navigation links.
- **hero.tsx**: Hero section component for the landing page with animated headings, descriptions, and call-to-action buttons using Framer Motion for animations.
- **providers.tsx**: Likely contains provider components for various contexts or services.
- **ui/**: Directory for reusable UI components.

#### Contexts (`src/contexts/`)

- **auth-context.tsx**: Authentication context provider that manages user authentication state using Supabase. Provides functions for sign-up, sign-in, and sign-out, as well as user state management.

#### Library (`src/lib/`)

- **supabase.ts**: Initializes the Supabase client for authentication and database operations. Defines the Profile type for user profiles.
- **db.ts**: Database utility functions.
- **types.ts**: Common TypeScript type definitions.
- **utils.ts**: Utility functions used throughout the application.
- **supabase/**: Directory for Supabase-specific utilities.

#### Middleware (`src/middleware.ts`)

Currently a minimal implementation that allows all requests to pass through. Route protection is commented out, suggesting it will be implemented in the future.

#### Types (`src/types/`)

- **index.ts**: TypeScript type definitions for the application.

### Public Assets (`public/`)

- **file.svg**: File icon for the application.
- **globe.svg**: Globe icon for the application.
- **next.svg**: Next.js logo.
- **vercel.svg**: Vercel logo.
- **window.svg**: Window icon for the application.

## Key Technologies

1. **Next.js**: React framework for server-side rendering and static site generation.
2. **TypeScript**: Adds static typing to JavaScript for better developer experience and code quality.
3. **Supabase**: Backend-as-a-Service for authentication and database operations.
4. **Tailwind CSS**: Utility-first CSS framework for styling.
5. **Framer Motion**: Library for animations and transitions.
6. **Headless UI**: Unstyled, accessible UI components.
7. **Heroicons**: SVG icon set.

## Authentication Flow

The application uses Supabase for authentication, implemented through the `AuthContext` provider. The authentication flow includes:

1. User registration with email, password, and full name.
2. User login with email and password.
3. Session management with automatic session restoration.
4. User state management across the application.

## UI Design

The application uses a dark theme by default with a modern, clean design. UI components are styled with Tailwind CSS, and animations are implemented using Framer Motion for a polished user experience.

## Routing

Routing is handled by Next.js App Router, with pages defined in the `src/app` directory. The application includes routes for:

- Home page (`/`)
- Authentication (`/login`, `/register`)
- Dashboard (`/dashboard`)
- Chatbot management (`/dashboard/chatbots`)

## Future Development

Based on the codebase structure, future development might include:

1. Implementing route protection in middleware.
2. Expanding chatbot management features.
3. Enhancing the dashboard with more analytics.
4. Integrating with additional services beyond Notion.