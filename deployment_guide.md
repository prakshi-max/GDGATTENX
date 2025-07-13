# 🚀 Deployment Guide - GDG Attendance Tracker

## Deploying to Streamlit Cloud

### Step 1: Prepare Your Repository

1. **Create a GitHub Repository**
   - Go to [GitHub](https://github.com)
   - Create a new repository named `gdg-attendance-tracker`
   - Make it public (required for free Streamlit Cloud)

2. **Upload Your Project Files**
   - Upload all project files to the repository
   - Ensure these files are included:
     - `app.py`
     - `requirements.txt`
     - `firebase_admin_init.py`
     - `serviceAccountkey.json`
     - `logo.png`
     - `.streamlit/config.toml`
     - `README.md`

### Step 2: Set Up Streamlit Cloud

1. **Go to Streamlit Cloud**
   - Visit [share.streamlit.io](https://share.streamlit.io)
   - Sign in with your GitHub account

2. **Deploy Your App**
   - Click "New app"
   - Select your repository: `gdg-attendance-tracker`
   - Set main file path: `app.py`
   - Click "Deploy"

### Step 3: Configure Secrets

1. **Add Firebase Credentials**
   - In Streamlit Cloud, go to your app settings
   - Navigate to "Secrets"
   - Add your Firebase service account key as JSON

2. **Add Google OAuth Credentials**
   - Add your Google OAuth client ID and secret
   - Format as TOML or use environment variables

### Step 4: Update OAuth Redirect URI

1. **Google Cloud Console**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Navigate to your OAuth 2.0 credentials
   - Add your Streamlit app URL as authorized redirect URI:
     ```
     https://your-app-name.streamlit.app
     ```

### Step 5: Test Your Deployment

1. **Verify All Features**
   - Test Google OAuth login
   - Test QR code generation (admin)
   - Test QR code scanning
   - Test attendance marking

## Alternative Deployment Options

### Heroku (Paid)
- More control over environment
- Custom domain support
- Better for production use

### Google Cloud Run
- Serverless deployment
- Auto-scaling
- Integration with Google services

### Vercel/Netlify
- Static site hosting
- Good for frontend-heavy apps

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Check `requirements.txt` includes all dependencies
   - Ensure all imports are correct

2. **Firebase Connection Issues**
   - Verify service account key is correct
   - Check Firebase project settings

3. **OAuth Errors**
   - Verify redirect URIs are correct
   - Check client ID and secret

4. **QR Code Issues**
   - Ensure OpenCV is properly installed
   - Check image format compatibility

## Security Considerations

1. **Environment Variables**
   - Never commit secrets to repository
   - Use Streamlit Cloud secrets management

2. **Firebase Rules**
   - Set up proper Firestore security rules
   - Restrict access to authorized users

3. **OAuth Configuration**
   - Use HTTPS in production
   - Configure proper redirect URIs

## Performance Optimization

1. **Image Processing**
   - Optimize QR code generation
   - Compress images for faster loading

2. **Database Queries**
   - Use efficient Firestore queries
   - Implement pagination for large datasets

3. **Caching**
   - Cache frequently accessed data
   - Use Streamlit's caching features

## Monitoring and Maintenance

1. **Logs**
   - Monitor Streamlit Cloud logs
   - Set up error tracking

2. **Updates**
   - Keep dependencies updated
   - Monitor for security patches

3. **Backup**
   - Regular Firebase data backups
   - Version control for code changes

---

**Your app will be available at: `https://your-app-name.streamlit.app`** 