# ChatSphere Frontend

The frontend application for ChatSphere, built with Next.js 14, TypeScript, and Tailwind CSS.

## Architecture

- `src/`
  - `app/` - Next.js app router pages and layouts
  - `components/` - Reusable UI components
  - `lib/` - Utility functions and shared logic
  - `hooks/` - Custom React hooks
  - `styles/` - Global styles and Tailwind configuration
  - `types/` - TypeScript type definitions
  - `services/` - API service integrations
  - `store/` - Global state management

## Key Features

- Modern Next.js 14 with App Router
- Type-safe development with TypeScript
- Beautiful UI with Tailwind CSS and shadcn/ui
- Firebase Authentication
- Real-time chat interface
- Responsive design
- Analytics dashboard
- Dark/Light mode support

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env.local
```
Update the variables with your Firebase and API configurations.

3. Start the development server:
```bash
npm run dev
```

The application will be available at http://localhost:3000

## Development

- Run tests: `npm test`
- Lint code: `npm run lint`
- Format code: `npm run format`
- Build for production: `npm run build`

## Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js pages and layouts
│   ├── components/       # Reusable components
│   ├── lib/             # Utility functions
│   ├── hooks/           # Custom React hooks
│   ├── styles/          # Global styles
│   ├── types/           # TypeScript types
│   └── services/        # API services
├── public/              # Static assets
└── tests/              # Test files
```

## Dependencies

Key dependencies include:
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- shadcn/ui
- Firebase
- React Query
- Zustand