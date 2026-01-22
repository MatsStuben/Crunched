# Aligned - PowerPoint AI Assistant

A PowerPoint add-in that uses AI vision to understand your slides and help you arrange shapes with natural language commands and generate presentation scripts.

## Features

### Shape Arrangement
- **Vision-powered shape detection**: AI analyzes your slide screenshot to identify and label all shapes
- **Natural language commands**: Arrange shapes by describing what you want (e.g., "arrange email, arrow, robot left to right")
- **Smart positioning**: Specify vertical/horizontal positioning (e.g., "at the top", "on the left side")

### Script Generation
- **Context-aware scripts**: Provide context about your audience and purpose
- **Slide-specific**: AI sees your actual slide content and generates relevant talking points
- **Conversational tone**: Scripts are written naturally, not robotically

## Architecture

```
┌─────────────────────┐     ┌─────────────────────────────────┐
│  PowerPoint Add-in  │     │           Backend               │
│    (TypeScript)     │────▶│          (FastAPI)              │
│                     │     │                                 │
│  - Capture slides   │     │  ┌─────────────────────────┐   │
│  - Get shape info   │     │  │    Scene Analyzer       │   │
│  - Execute moves    │     │  │  (Vision + Labels)      │   │
└─────────────────────┘     │  └─────────────────────────┘   │
                            │  ┌─────────────────────────┐   │
                            │  │      Arranger           │   │
                            │  │  (NL → Order + Align)   │   │
                            │  └─────────────────────────┘   │
                            │  ┌─────────────────────────┐   │
                            │  │   Script Generator      │   │
                            │  │  (Slide → Script)       │   │
                            │  └─────────────────────────┘   │
                            └─────────────────────────────────┘
```

## Setup

### Prerequisites
- Node.js 18+
- Python 3.11+
- uv (Python package manager)
- Anthropic API key

### Backend Setup

```bash
cd backend
export ANTHROPIC_API_KEY=your_key_here
uv run uvicorn main:app --host 0.0.0.0 --port 8001 --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

Generate SSL certificates if needed:
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

### Add-in Setup

```bash
npm install
npm start
```

The add-in runs on `https://localhost:3001` by default.

### Load in PowerPoint
1. Open PowerPoint
2. Go to Insert → Add-ins → Upload My Add-in
3. Select `manifest.xml`

## Usage

### Arranging Shapes
1. Click **Start** to analyze the current slide
2. AI identifies all shapes and shows their labels
3. Type your arrangement command:
   - "arrange email, arrow, robot left to right"
   - "put the chart at the top, then the text below"
   - "align all shapes left to right at the bottom"
4. Click **Arrange**

### Generating Scripts
1. Enter context in the text area:
   - Audience (executives, engineers, customers)
   - Purpose (pitch, update, training)
   - Key points to emphasize
2. Click **Generate Script**
3. AI produces a presentation script based on your slide content and context

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze` | POST | Analyze slide screenshot and label shapes |
| `/start` | POST | Initialize session with slide analysis |
| `/arrange` | POST | Get arrangement order from natural language |
| `/generate-script` | POST | Generate presentation script |
| `/health` | GET | Health check |

## Tech Stack

- **Frontend**: TypeScript, React, Fluent UI, Office.js
- **Backend**: Python, FastAPI, Pydantic
- **AI**: Claude Sonnet 4.5 (vision + text)

## Project Structure

```
├── backend/
│   ├── agents/
│   │   ├── scene_analyzer.py   # Vision-based shape labeling
│   │   ├── arranger.py         # NL command → arrangement
│   │   └── script_generator.py # Slide → presentation script
│   ├── models.py               # Pydantic data models
│   └── main.py                 # FastAPI endpoints
├── src/
│   └── taskpane/
│       ├── components/
│       │   └── App.tsx         # Main UI
│       └── taskpane.ts         # PowerPoint API functions
├── manifest.xml                # Office add-in manifest
└── README.md
```

## How It Works

### Shape Arrangement Flow
1. **Screenshot**: Add-in captures slide as PNG
2. **Shape data**: Add-in gets all shape positions/dimensions from PowerPoint API
3. **Scene analysis**: Backend sends image + positions to Claude, gets labeled shapes
4. **User command**: User types natural language arrangement instruction
5. **Arranger**: Claude interprets command → returns shape order + alignment type
6. **Execute**: Add-in moves shapes to calculated positions in Claude's specified order

### Script Generation Flow
1. **Screenshot**: Add-in captures current slide
2. **Context**: User provides audience/purpose information
3. **Generation**: Claude sees slide + context, writes presentation script