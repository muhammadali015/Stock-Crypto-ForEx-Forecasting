# Vercel Deployment Guide

## 🚀 Deploying FinTech Forecasting App to Vercel

This guide will help you deploy your FinTech forecasting application to Vercel with both frontend and backend.

## 📋 Prerequisites

- Vercel account (free tier available)
- GitHub repository connected to Vercel
- Node.js 16+ and Python 3.9+ (handled by Vercel)

## 🔧 Deployment Steps

### 1. **Connect Repository to Vercel**

1. Go to [vercel.com](https://vercel.com)
2. Sign in with your GitHub account
3. Click "New Project"
4. Import your repository: `muhammadali015/Stock-Crypto-ForEx-Forecasting`

### 2. **Configure Build Settings**

Vercel will automatically detect the configuration from `vercel.json`:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    },
    {
      "src": "frontend/package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "build"
      }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "app.py"
    },
    {
      "src": "/(.*)",
      "dest": "frontend/build/$1"
    }
  ],
  "env": {
    "PYTHON_VERSION": "3.9"
  }
}
```

### 3. **Environment Variables (Optional)**

If you need any environment variables, add them in Vercel dashboard:
- Go to Project Settings → Environment Variables
- Add any required variables

### 4. **Deploy**

1. Click "Deploy" in Vercel dashboard
2. Wait for build to complete (5-10 minutes)
3. Your app will be available at `https://your-project-name.vercel.app`

## 🏗️ Project Structure for Vercel

```
├── app.py                 # Flask entrypoint (root level)
├── vercel.json           # Vercel configuration
├── package.json          # Root package.json
├── requirements.txt      # Python dependencies
├── backend/
│   └── app_sqlite.py    # Main Flask application
├── frontend/
│   ├── package.json     # Frontend dependencies
│   └── src/             # React source code
└── ml_models/           # ML model files
```

## 🔧 How It Works

### **Backend (Flask)**
- `app.py` imports and runs the Flask app from `backend/app_sqlite.py`
- Vercel uses `@vercel/python` builder for Flask
- API routes (`/api/*`) are handled by Flask

### **Frontend (React)**
- Vercel builds the React app using `npm run build`
- Static files are served from `frontend/build/`
- All non-API routes serve the React app

### **Routing**
- `/api/*` → Flask backend
- `/*` → React frontend (SPA)

## 🚨 Troubleshooting

### **Common Issues**

#### 1. **Build Failures**
```bash
# Check build logs in Vercel dashboard
# Common fixes:
- Ensure all dependencies are in requirements.txt
- Check Python version compatibility
- Verify file paths in vercel.json
```

#### 2. **API Routes Not Working**
```bash
# Verify vercel.json routes configuration
# Check that app.py imports the correct Flask app
# Ensure CORS is configured for production domain
```

#### 3. **Frontend Not Loading**
```bash
# Check that frontend builds successfully
# Verify build output directory in vercel.json
# Check for JavaScript errors in browser console
```

### **Debug Commands**

```bash
# Test locally with Vercel CLI
npm install -g vercel
vercel dev

# Check build locally
cd frontend && npm run build
python app.py
```

## 📊 Performance Optimization

### **Frontend**
- Enable compression in Vercel settings
- Use Vercel's CDN for static assets
- Optimize images and assets

### **Backend**
- Use Vercel's serverless functions efficiently
- Implement caching for expensive operations
- Optimize database queries

## 🔒 Security Considerations

### **Production Settings**
- Update CORS settings for production domain
- Use environment variables for sensitive data
- Enable HTTPS (automatic with Vercel)

### **API Security**
- Implement rate limiting
- Add input validation
- Use secure headers

## 📈 Monitoring

### **Vercel Analytics**
- Enable Vercel Analytics for performance monitoring
- Monitor API response times
- Track error rates

### **Logs**
- Check Vercel function logs
- Monitor build logs
- Set up error alerts

## 🎯 Production Checklist

- [ ] Repository connected to Vercel
- [ ] Build configuration verified
- [ ] Environment variables set
- [ ] CORS configured for production
- [ ] Database (SQLite) working
- [ ] API endpoints tested
- [ ] Frontend builds successfully
- [ ] Performance optimized
- [ ] Security measures in place

## 🚀 Deployment Commands

```bash
# Deploy to Vercel
vercel --prod

# Deploy with specific environment
vercel --prod --env production

# Check deployment status
vercel ls
```

## 📞 Support

If you encounter issues:

1. **Check Vercel Build Logs** - Most issues are visible in build logs
2. **Test Locally** - Use `vercel dev` to test locally
3. **Vercel Documentation** - [vercel.com/docs](https://vercel.com/docs)
4. **GitHub Issues** - Report issues in your repository

---

**Your FinTech forecasting app is now ready for production deployment on Vercel!** 🎉
