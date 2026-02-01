# 🔐 Setup Instructions

## Environment Configuration

Before running GreenScale, you need to configure your environment variables.

### 1. Copy the example environment file:
```bash
cp .env.example .env
```

### 2. Edit `.env` and add your credentials:
```bash
# Redis Configuration (for local development)
REDIS_HOST=localhost
REDIS_PORT=6379

# Neysa AI API Configuration
NEYSA_API_URL="https://boomai-llama.neysa.io/v1/chat/completions"
NEYSA_API_KEY="your-api-key-here"
```

### 3. Get Your Neysa API Key:
- Register at [Neysa AI Platform](https://neysa.io)
- Navigate to API Keys section
- Generate a new API key for the Llama 3.3 70B model
- Replace `your-api-key-here` with your actual key

### 4. Security Notes:
- **NEVER commit `.env` file to git**
- The `.env` file is already in `.gitignore`
- Use `.env.example` as a template for team members
- Rotate API keys regularly

## Quick Start

Once configured, follow the main [README.md](README.md) for deployment instructions.
