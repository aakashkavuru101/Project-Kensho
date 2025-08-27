# Project Kensho - Production Deployment Guide

## Free Hosting Platforms for Web UI

Project Kensho can be deployed to several free hosting platforms. Here are the recommended options:

### 1. **Render** (Recommended)
- **URL**: https://render.com
- **Free Tier**: 750 hours/month, automatic deployments
- **Pros**: Easy Flask deployment, automatic HTTPS, environment variables
- **Setup**: Connect GitHub repository, specify `python webapp/app.py`
- **Buildpack**: Python (auto-detected)

### 2. **Railway**
- **URL**: https://railway.app
- **Free Tier**: $5 monthly credit (good for small apps)
- **Pros**: Simple deployment, automatic scaling, database add-ons
- **Setup**: Connect GitHub, Railway auto-detects Flask app

### 3. **Vercel** (With Serverless Functions)
- **URL**: https://vercel.com
- **Free Tier**: Unlimited bandwidth, 100GB-hours execution time
- **Note**: Requires minimal modification for serverless deployment
- **Good for**: Static frontend + API endpoints

### 4. **PythonAnywhere**
- **URL**: https://www.pythonanywhere.com
- **Free Tier**: One web app, limited CPU seconds
- **Pros**: Python-focused, easy Flask deployment
- **Good for**: Small-scale testing and demos

### 5. **Heroku** (Limited Free Tier)
- **URL**: https://heroku.com
- **Note**: No longer offers free tier, but has low-cost options
- **Good for**: Production deployments with paid plans

## Deployment Instructions

### For Render (Recommended)

1. **Create `render.yaml`** in project root:
```yaml
services:
  - type: web
    name: project-kensho
    env: python
    buildCommand: "pip install -r requirements.txt && python -m spacy download en_core_web_sm"
    startCommand: "python webapp/app.py"
    envVars:
      - key: FLASK_ENV
        value: production
      - key: PORT
        value: 5001
```

2. **Update `webapp/app.py`** for production:
```python
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
```

3. **Environment Variables**:
   - Set configuration values in Render dashboard
   - Upload `config.ini` with real API credentials

### For Railway

1. **Create `railway.toml`**:
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python webapp/app.py"
healthcheckPath = "/"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

## Security Considerations for Production

1. **Environment Variables**: Store API keys in environment variables, not config files
2. **HTTPS**: All recommended platforms provide automatic HTTPS
3. **Rate Limiting**: Consider adding Flask-Limiter for API endpoint protection
4. **File Upload Limits**: Already implemented (16MB max)
5. **CORS**: Add Flask-CORS if needed for cross-origin requests

## Performance Optimizations

1. **Static Files**: Use CDN for static assets in production
2. **Caching**: Add Redis for task status caching (available on most platforms)
3. **Database**: Consider PostgreSQL for persistent task storage
4. **Monitoring**: Use platform-specific monitoring tools

## Configuration Management

Update `webapp/app.py` to load configuration from environment:

```python
import os
from flask import Flask

app = Flask(__name__)

# Production configuration
if os.environ.get('FLASK_ENV') == 'production':
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'production-secret-key'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'uploads')
    )
```

## Cost Estimation

| Platform | Free Tier | Monthly Cost | Best For |
|----------|-----------|--------------|----------|
| Render | 750 hours | $0 | Small to medium usage |
| Railway | $5 credit | ~$5 | Consistent small usage |
| Vercel | Unlimited | $0 | Serverless architecture |
| PythonAnywhere | Limited | $5+ | Python-specific needs |

## Recommended Architecture for Scale

For production scale:
1. **Frontend**: Vercel/Netlify (static hosting)
2. **API**: Render/Railway (Flask backend)
3. **Database**: PostgreSQL (for task persistence)
4. **File Storage**: AWS S3/Cloudinary (for uploaded documents)
5. **Monitoring**: Sentry for error tracking

This setup provides a robust, scalable, and cost-effective deployment for Project Kensho.