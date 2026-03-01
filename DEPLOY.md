# Deployment Guide

## Quick Start (Windows)

### 1. Clone the repository
```powershell
git clone https://github.com/your-username/multi-modal-agent.git
cd multi-modal-agent
```

### 2. Install dependencies
```powershell
# Node.js dependencies
npm install

# Python dependencies (for embedding server)
pip install -r requirements.txt
```

### 3. Configure environment
```powershell
# Copy example and edit
copy .env.example .env
# Edit .env with your API keys
```

### 4. Build and run
```powershell
# Production build
npm run build

# Start server
npm run start
```

Access at: `http://localhost:5000`

---

## Network Access (LAN)

The server listens on `0.0.0.0:5000` by default, making it accessible from other devices on your network.

### Find your local IP:
```powershell
ipconfig
# Look for "IPv4 Address" (e.g., 192.168.1.100)
```

### Access from other devices:
```
http://192.168.1.100:5000
```

### Firewall setup (if needed):
```powershell
netsh advfirewall firewall add rule name="Multi-Modal Agent" dir=in action=allow protocol=TCP localport=5000
```

---

## Production Deployment

### Using the deploy script:
```powershell
.\deploy.ps1
```

### Manual setup:

1. **Install Node.js** (v18+): https://nodejs.org/
2. **Install Python** (3.9+): https://python.org/
3. **Clone and setup**:
   ```powershell
   git clone <repository-url>
   cd multi-modal-agent
   npm install --production
   npm run build
   npm run start
   ```

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENROUTER_API_KEY` | OpenRouter API key | Yes |
| `SUPABASE_URL` | Supabase project URL | Yes (for RAG) |
| `SUPABASE_KEY` | Supabase anon key | Yes (for RAG) |
| `HF_TOKEN` | Hugging Face token | No (for embeddings) |
| `PORT` | Server port (default: 5000) | No |

---

## Troubleshooting

### Port already in use
```powershell
# Change port
$env:PORT=3000
npm run start
```

### Build fails
```powershell
# Clear cache and rebuild
rm -r node_modules
rm package-lock.json
npm install
npm run build
```

### Can't access from network
1. Check firewall rules
2. Verify IP address with `ipconfig`
3. Ensure router allows LAN connections

---

## Docker (Optional)

Create `Dockerfile`:
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
RUN npm run build
EXPOSE 5000
CMD ["npm", "start"]
```

Build and run:
```bash
docker build -t multi-modal-agent .
docker run -p 5000:5000 --env-file .env multi-modal-agent
```
