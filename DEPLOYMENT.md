# Deployment Guide

## 🚀 Frontend Deployment (Vercel)
The **frontend** is successfully deployed on Vercel and can be accessed at:
**[https://stock-prediction-dashboard-iota.vercel.app](https://stock-prediction-dashboard-iota.vercel.app)**

### Configuration
- The project is configured as a **Vite** Single Page Application (SPA).
- `vercel.json` handles the static build and routing.

---

## ⚠️ Backend Deployment Issues (Vercel)
Attempting to deploy the Python backend to Vercel Serverless resulted in **500 Errors**.

**Reason:**
- **Size Limit Limit**: Vercel Serverless Functions have a **50MB** (zipped) size limit.
- **Dependencies**: The project uses heavy libraries: `tensorflow` (~400MB), `pandas`, `numpy`, `scikit-learn`. These exceed the limit significantly.

## ✅ Recommended Backend Hosting: Render
We strongly recommend deploying the backend to **Render.com** (or Railway/AWS) which supports Docker containers without strict size limits.

### How to Deploy Backend to Render
1. Create a new **Web Service** on [Render](https://dashboard.render.com/).
2. Connect your GitHub repository.
3. Select the `backend` directory as the **Root Directory**.
4. Runtime: **Docker**.
5. Render will detect the `Dockerfile` in `backend/` and build it.
6. Once deployed, get the **Render URL** (e.g., `https://my-api.onrender.com`).

### Connecting Frontend to Backend
1. Go to Vercel Project Settings.
2. Add an Environment Variable:
   - Name: `VITE_API_URL`
   - Value: `https://my-api.onrender.com` (Your Render URL)
3. Redeploy the Frontend.
