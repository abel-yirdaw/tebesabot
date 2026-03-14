#!/bin/bash
# scripts/deploy.sh - Deploy to Vercel

echo "🚀 Deploying Habesha Dating Bot to Vercel"
echo "========================================"

# Check if vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | xargs)
fi

# Deploy to Vercel
echo "📤 Deploying..."
vercel --prod --confirm

# Get deployment URL
DEPLOY_URL=$(vercel ls | grep -o 'https://[^ ]*\.vercel\.app' | head -1)

# Set webhook
echo "🔗 Setting webhook..."
curl -F "url=$DEPLOY_URL/api/webhook" "https://api.telegram.org/bot$BOT_TOKEN/setWebhook"

echo ""
echo "✅ Deployment complete!"
echo "Bot URL: $DEPLOY_URL"