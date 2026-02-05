# Claude Agent SDK UI

A React-based web interface for the Claude Agent SDK.

## Setup

### Backend (Python)

1. Install Python dependencies:
```bash
cd ui/backend
pip install -r requirements.txt
pip install -e ../..  # Install the claude-agent-sdk
```

2. Run the backend server:
```bash
python server.py
```

The backend will run on `http://localhost:8000`

### Frontend (React)

1. Install Node dependencies:
```bash
cd ui
npm install
```

2. Run the React app:
```bash
npm start
```

The frontend will run on `http://localhost:3000`

## Usage

1. Start both the backend server (port 8000) and frontend app (port 3000)
2. Open your browser to `http://localhost:3000`
3. Type your questions and interact with Claude Agent
4. Use the Settings panel to configure system prompts and max turns

## Features

- Real-time WebSocket communication
- Streaming responses from Claude
- Configurable system prompts
- Adjustable max turns
- Clean, modern UI
- Connection status indicator
