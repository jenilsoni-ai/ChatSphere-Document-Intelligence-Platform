# ChatSphere - Your AI-Powered Chat Platform

ChatSphere is a modern, full-stack application that enables users to create and manage AI-powered chatbots with custom knowledge bases. Built with Next.js, FastAPI, and Firebase, it offers a seamless experience for creating, training, and interacting with personalized chatbots.

## Features

- 🤖 Create custom AI chatbots with personalized knowledge bases
- 📚 Support for multiple data sources and formats
- 🔒 Secure authentication with Firebase
- 💬 Real-time chat interface
- 📊 Analytics and usage statistics
- 🎨 Modern, responsive UI with Tailwind CSS

## Project Structure

- `frontend/` - Next.js frontend application
- `backend/` - FastAPI backend server
- `example_datasources/` - Sample data sources for testing
- `screenshots/` - Application screenshots and documentation

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.12+
- Conda (recommended for environment management)

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Backend Setup

1. Create and activate a Python virtual environment:
```bash
conda create -n chatsphere python==3.12 -y
conda activate chatsphere
```

2. Install dependencies and start the server:
```bash
cd backend
pip install -r requirements.txt
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

