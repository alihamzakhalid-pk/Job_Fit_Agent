# 🚀 Deployment Guide - JobFit Agent

Deploy your project to the cloud in 10 minutes!

---

## Option 1: Vercel (Frontend) + Railway (Backend) - **EASIEST**

### ✅ Prerequisites
- GitHub account (free)
- Push your project to GitHub

### Step 1: Deploy Backend to Railway

**1. Go to [railway.app](https://railway.app)**

**2. Click "Start a New Project" → "Deploy from GitHub"**

**3. Connect your GitHub account and select your repo**

**4. Railway auto-detects Dockerfile**

**5. Set Environment Variables:**
   - Go to `Variables` tab
   - Add your environment variables:
     ```
     GROQ_API_KEY=your_key_here
     ```

**6. Wait for deployment (2-3 min)**

**7. Get your API URL:**
   - Click on your deployment
   - Copy the public URL (e.g., `https://jobfit-api-prod.up.railway.app`)
   - This is your `BACKEND_URL`

---

### Step 2: Deploy Frontend to Vercel

**1. Go to [vercel.com](https://vercel.com)**

**2. Click "New Project" → "Import a Git Repository"**

**3. Select your GitHub repo**

**4. Configure Build Settings:**
   - **Root Directory:** `jobfit_react/frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

**5. Add Environment Variables:**
   - Click "Environment Variables"
   - Add:
     ```
     VITE_API_URL=https://jobfit-api-prod.up.railway.app
     ```
   (Replace with YOUR Railway backend URL)

**6. Click "Deploy"**

**7. Wait for deployment (1-2 min)**

**8. Get your public URL:**
   - Vercel shows it when done
   - e.g., `https://jobfit-agent.vercel.app`

---

## Option 2: All-in-One - Railway Only

If you want everything on Railway:

**1. Create a `Procfile` in project root:**
```
web: uvicorn jobfit_react.backend.main:app --host 0.0.0.0 --port $PORT
```

**2. Deploy entire repo to Railway**

**3. In Railway dashboard:**
   - Set Port: 8000
   - Add GROQ_API_KEY environment variable

**4. Frontend & backend run on same domain**

---

## Option 3: Render.com (FREE Alternative)

Similar to Railway but free tier has limitations:

**1. Go to [render.com](https://render.com)**
**2. New → Web Service**
**3. Connect GitHub**
**4. Setup is similar to Railway**
**5. Free tier: 15GB bandwidth/month, sleeps after 15 min inactivity**

---

## ⚠️ Important Notes

### Environment Variables Needed:
```
GROQ_API_KEY=your_groq_api_key
LLM_MODEL=llama-3.3-70b-versatile (optional, has default)
```

### Get GROQ API Key:
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (free)
3. Create API key
4. Copy to environment variables

### CORS Configuration:
Backend already configured for Vercel URL. If using different domain, update in `main.py`:

```python
allow_origins=["https://yourdomain.vercel.app", "http://localhost:5173"]
```

### Cost:
- **Railway:** Free tier = 5GB/month + $5 credit. Plenty for testing.
- **Vercel:** Free forever for frontend
- **Render:** Free tier with limitations

---

## 🧪 Testing After Deployment

1. Open your Vercel URL: `https://your-site.vercel.app`
2. Upload a resume PDF
3. Paste a real job description
4. Click "Analyze My Fit"
5. Should see processing pipeline
6. Results in 30-60 seconds

---

## 🐛 Troubleshooting

### "Cannot connect to backend"
- Check CORS origins in `main.py`
- Verify API URL in Vercel environment variables
- Check Railway backend is running (green status)

### "GROQ API Key error"
- Verify API key is valid in Railway environment
- Check it has budget remaining
- Regenerate if unsure

### Frontend builds but backend fails
- Check `requirements.txt` is present
- Verify Dockerfile syntax
- Check Railway logs for errors

### API URL not updating
- Clear browser cache
- Rebuild on Vercel (manual redeploy)
- Check environment variable is set

---

## 📊 Production Checklist

- ✅ GROQ_API_KEY set in backend
- ✅ VITE_API_URL set in frontend
- ✅ Firebase/database setup (optional, for persistence)
- ✅ Error logging enabled
- ✅ CORS properly configured
- ✅ Rate limiting configured (optional)

---

## 🎉 You're Live!

Once deployed:
- **Frontend:** Share your Vercel URL with users
- **Backend:** Handles requests from any domain
- **Users:** Just click link, upload, get results!

---

**Questions?**
- Railway Support: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/
