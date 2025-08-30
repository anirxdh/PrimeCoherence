#!/bin/bash
# Deployment script for Prime Coherence

echo "🚀 Deploying Prime Coherence to Render..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit"
fi

# Check if remote exists
if ! git remote get-url origin > /dev/null 2>&1; then
    echo "Please add your Render git remote:"
    echo "git remote add origin https://git.render.com/your-repo-url.git"
    exit 1
fi

# Push to Render
echo "Pushing to Render..."
git add .
git commit -m "Deploy to Render"
git push origin main

echo "✅ Deployment complete!"
echo "Your app will be available at: https://your-app-name.onrender.com"
