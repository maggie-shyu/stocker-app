# Stocker Full-Stack Deployment Guide

We've prepared your codebase for a production deployment! The backend configuration has been updated to dynamically read CORS settings, and your frontend's API client will read its URL from environment variables.

Follow these steps to deploy your application.

---

## 1. Supabase Database Setup

You already have a Supabase URL configured in your `.env` files. We need to make sure your database schema is up-to-date.

**Option A: Using the Supabase CLI (Recommended)**
If you have the Supabase CLI installed, you can simply run:
```bash
supabase db push
```

**Option B: Using the Supabase Dashboard**
1. Go to your project on the [Supabase Dashboard](https://app.supabase.com/).
2. Navigate to the **SQL Editor** on the left menu.
3. Open each file in `supabase/migrations/` sequentially (`001`, `002`, `003`, `004`), copy the SQL contents, paste them into the SQL Editor, and hit **Run**.

---

## 2. Render Backend Deployment

We have created a `render.yaml` "Blueprint" to make this a 1-click process.

1. Create a free account on [Render](https://render.com/) if you haven't already.
2. In the Render Dashboard, click **New +** and select **Web Service**.
3. Connect your GitHub repository containing the Stocker code.
4. Render will automatically detect the `render.yaml` file.
5. Click on **Environment variables**. Add the following:
   - `SUPABASE_URL`: (Copy from your `.env` file)
   - `CORS_ORIGINS`: Leave this blank for now (we'll come back to update this after Netlify deployment).
6. Click on **Advanced > Add Secret File**. Add the following:
   - `SUPABASE_SECRET_KEY`: (Copy from your `.env` file - use the service role key)
   - `ADMIN_EMAIL_ALLOWLIST`: (Copy from your `.env` file)
7. Click **Apply**.
8. Wait for the build to finish. Once done, copy the resulting URL (e.g., `https://stocker-backend-xxxx.onrender.com`).

---

## 3. Netlify Frontend Deployment

1. Create a free account on [Netlify](https://www.netlify.com/).
2. Click **Add new site** -> **Import an existing project**.
3. Connect your GitHub account and select your repository.
4. Netlify should automatically detect the settings from our `netlify.toml` (`base="frontend"`, `command="npm run build"`, etc.).
5. Click on **Environment variables**. Add the following:
   - `VITE_API_URL`: Paste the Render backend URL you copied in the previous step (e.g., `https://stocker-backend-xxxx.onrender.com/api`). **Important: add `/api` to the end!**
   - `VITE_SUPABASE_URL`: (Copy from your `frontend/.env` file)
   - `VITE_SUPABASE_PUBLISHABLE_KEY`: (Copy from your `frontend/.env` file)
6. Click **Deploy site**.
7. Once deployed, Netlify will give you a public URL (e.g., `https://stocker-xxxx.netlify.app`). Copy this URL.

---

## 4. Finalizing CORS (Important!)

Now that you have your Netlify frontend URL, we must tell the Render backend to accept requests from it.

1. Go back to your [Render Dashboard](https://dashboard.render.com/) and open your Web Service.
2. Go to the **Environment** tab.
3. Find or add the `CORS_ORIGINS` variable.
4. Set its value to your Netlify URL without a trailing slash (e.g., `https://stocker-xxxx.netlify.app`).
5. Save changes. Render might automatically redeploy, or you may need to click "Manual Deploy".

**Congratulations!** Your Stocker application should now be live and fully functional.
