# 🚀 Deploy Prime Coherence to Render

This guide will help you deploy your Prime Coherence application to Render using the local SQLite database.

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **Git Repository**: Your code should be in a Git repository (GitHub, GitLab, etc.)

## Deployment Steps

### 1. Connect Your Repository to Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your Git repository
4. Select the repository containing Prime Coherence

### 2. Configure the Web Service

**Service Settings:**
- **Name**: `prime-coherence-api` (or your preferred name)
- **Environment**: `Python 3`
- **Region**: Choose closest to your users
- **Branch**: `main` (or your default branch)
- **Root Directory**: Leave empty (deploy from root)

**Build & Deploy Settings:**
- **Build Command**: `cd backend && pip install -r requirements.txt`
- **Start Command**: `cd backend && gunicorn app:app --bind 0.0.0.0:$PORT`

**Environment Variables:**
- `FLASK_ENV`: `production`
- `DATABASE_URL`: `sqlite:///prime_coherence.db`

### 3. Deploy

1. Click **"Create Web Service"**
2. Render will automatically build and deploy your application
3. Wait for the build to complete (usually 2-5 minutes)

### 4. Access Your Application

Once deployed, your API will be available at:
```
https://your-app-name.onrender.com
```

## Local SQLite Database

✅ **Your application uses a local SQLite database**  
✅ **No external database connection required**  
✅ **Database file is created automatically on first run**  
✅ **Data persists between deployments**  

## API Endpoints

Your deployed API will have these endpoints:
- `GET /health` - Health check
- `POST /upload` - Upload and analyze circuits
- `POST /convert` - Convert circuit formats
- `GET /results` - Get analysis results
- `GET /result/<id>` - Get specific result
- `POST /clear-database` - Clear database
- `GET /database-stats` - Get database statistics

## Frontend Integration

To use the deployed API with your local frontend:

1. Update the API URL in your frontend:
   ```python
   # In frontend/dashboard.py
   st.session_state.api_base_url = "https://your-app-name.onrender.com"
   ```

2. Run your local frontend:
   ```bash
   cd frontend
   make run
   ```

## Troubleshooting

### Common Issues:

1. **Build Fails**: Check that all dependencies are in `backend/requirements.txt`
2. **App Won't Start**: Verify the start command uses `gunicorn`
3. **Database Issues**: SQLite file is created automatically on first request

### Logs:
- View logs in Render Dashboard → Your Service → Logs
- Check for any error messages during build or runtime

## Cost

✅ **Free Tier**: Render offers a free tier that's perfect for this application  
✅ **No Database Costs**: SQLite is included with your application  
✅ **Automatic Scaling**: Render handles traffic automatically  

## Next Steps

After deployment:
1. Test your API endpoints
2. Update your frontend to use the deployed API
3. Share your application URL with others!

---

**Need Help?** Check Render's [documentation](https://render.com/docs) or their [community forum](https://community.render.com).
