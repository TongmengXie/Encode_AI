# WanderMatch Render Deployment Guide

This guide provides detailed instructions for deploying WanderMatch to Render's cloud platform and managing your deployment.

## Pre-Deployment Checklist

- [ ] Ensure all code changes are committed to your repository
- [ ] Verify the local application works correctly
- [ ] Test the survey submission flow locally
- [ ] Make sure API keys are available

## Render Account Setup

1. **Create a Render Account**:
   - [ ] Sign up at [render.com](https://render.com)
   - [ ] Verify your email

2. **Connect Your Repository**:
   - [ ] Click "New" in the Render dashboard
   - [ ] Select "Blueprint"
   - [ ] Connect your GitHub/GitLab account
   - [ ] Select the WanderMatch repository

## Deployment Process

1. **Blueprint Configuration**:
   - [ ] Render will detect your `render.yaml` file
   - [ ] Review all services that will be created:
     - [ ] wandermatch-api (web service)
     - [ ] wandermatch-frontend (static site)
     - [ ] wandermatch-storage (optional persistent disk)
   - [ ] Click "Apply Blueprint"

2. **Environment Variables**:
   - [ ] After services are created, click on the wandermatch-api service
   - [ ] Go to "Environment" tab
   - [ ] Add your secret keys:
     - [ ] OPENAI_API_KEY
     - [ ] GEMINI_API_KEY
     - [ ] GOOGLE_API_KEY (if using)
   - [ ] Click "Save Changes"
   - [ ] Wait for the service to rebuild

3. **Verify Deployment**:
   - [ ] Check the build logs for each service
   - [ ] Ensure the frontend build completed successfully
   - [ ] Verify that the survey HTML files were copied correctly
   - [ ] Check that directories were created properly

## Testing

1. **Access Your Application**:
   - [ ] Click on the wandermatch-frontend URL
   - [ ] Verify the survey launcher loads correctly
   - [ ] Try launching the survey form

2. **Submit Test Data**:
   - [ ] Fill out the survey form
   - [ ] Submit the form
   - [ ] Verify the data was saved successfully

3. **API Health Check**:
   - [ ] Visit the `/api/health` endpoint of your wandermatch-api service
   - [ ] Confirm the API is running and directories are accessible

4. **Test Embedding Calculation**:
   - [ ] Submit a test survey
   - [ ] Click "Calculate Travel Match" on the launcher
   - [ ] Verify that partners are found and displayed

5. **Test Blog Generation**:
   - [ ] Select a route after matching with a partner
   - [ ] Open the Blog Assistant
   - [ ] Click "Generate Travel Blog"
   - [ ] Verify the blog is generated successfully

6. **Test Q&A Feature**:
   - [ ] After selecting a route, check that the Q&A section appears
   - [ ] Enter a travel-related question
   - [ ] Verify you receive an answer from one of the LLM providers

## Sharing with Your Team

### Via Blueprint

1. **Create a Blueprint from your project**:
   - Log in to Render dashboard
   - Go to Blueprints section
   - Click "New Blueprint"
   - Select your existing services (wandermatch-api and wandermatch-frontend)
   - Name your blueprint (e.g., "WanderMatch Complete")

2. **Share the Blueprint**:
   - From the Blueprints section, find your blueprint
   - Click "Share" button
   - Choose "Team members" option
   - Add team members by email

3. **Set permissions**:
   - Choose appropriate permissions (View, Deploy, or Admin)
   - Team members will receive an email invitation

### Via GitHub

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Complete WanderMatch project with backend and frontend"
   git push origin main
   ```

2. **Invite collaborators**:
   - Go to your GitHub repository
   - Navigate to Settings → Collaborators
   - Add team members using their GitHub usernames or email

3. **Team members can deploy their own instances**:
   - They'll need to create their own Render account
   - Connect their account to GitHub
   - Deploy using the same render.yaml file

## CORS Configuration

The application uses a robust CORS configuration to ensure proper cross-origin requests:

1. **Default Configuration**:
   - In development mode: All origins are allowed
   - In production mode: Only specific origins are allowed (configurable)

2. **Customizing Allowed Origins**:
   - For team deployments, update the following section in `deploy/backend/app.py`:

   ```python
   allowed_origins = [
       'https://wandermatch-frontend-b17a.onrender.com',
       'https://wandermatch-frontend.onrender.com',
       'https://wandermatch-frontend-*.onrender.com',
       # Add your team members' domains here
       'https://teammate1-wandermatch-frontend.onrender.com',
       'https://teammate2-wandermatch-frontend.onrender.com'
   ]
   ```

3. **Testing CORS Configuration**:
   - Use the `/api/cors-test` endpoint to verify CORS is working
   - The endpoint returns detailed information about the request and server configuration

## Troubleshooting

### Common Issues

1. **Build Failures**:
   - [ ] Check the build logs
   - [ ] Verify Python version is correct
   - [ ] Ensure all dependencies are available

2. **File Not Found Errors**:
   - [ ] Check that HTML files were copied correctly
   - [ ] Verify directory structure matches expected paths

3. **API Connection Issues**:
   - [ ] Check CORS configuration
   - [ ] Verify the API URL is correctly set
   - [ ] Test API endpoints directly

4. **OpenAI API Issues**:
   - [ ] Verify API key is set correctly
   - [ ] Check usage limits and quotas
   - [ ] Look for API-specific errors in logs

5. **Blog Generation Issues**:
   - [ ] Check server logs for import errors
   - [ ] Verify the `blog_generator.py` file is accessible
   - [ ] Check output directory permissions
   - [ ] Test if alternative LLM providers are working (Gemini fallback)
   - [ ] Use the API directly to isolate frontend vs. backend issues

6. **NetworkError When Generating Blog**:
   - [ ] Check browser console for detailed error messages
   - [ ] Verify the API URL is correctly constructed
   - [ ] Test the `/api/health` endpoint to verify connectivity
   - [ ] Check if CORS is configured correctly
   - [ ] Verify that proper headers are being sent with the request

## Post-Deployment

1. **Monitoring**:
   - [ ] Set up alerts for service outages
   - [ ] Check logs periodically
   - [ ] Monitor API usage and costs

2. **Updates**:
   - [ ] For future updates, push changes to your repository
   - [ ] Render will automatically rebuild services
   - [ ] You can also trigger manual deploys from the dashboard

3. **Scaling**:
   - [ ] Monitor performance
   - [ ] Adjust instance sizes if needed
   - [ ] Consider upgrading plans for production usage

## Maintenance Tasks

1. **Backup Survey Data**:
   - [ ] Set up regular backups of the survey results
   - [ ] Consider exporting data periodically

2. **Security**:
   - [ ] Rotate API keys periodically
   - [ ] Monitor for unauthorized access
   - [ ] Keep dependencies updated 

## Recent Updates

The latest version includes several enhancements for Render deployment:

1. **Improved CORS Handling**:
   - Better regex for subdomain matching
   - Support for both HTTP and HTTPS protocols
   - More permissive headers configuration

2. **Enhanced Error Diagnostics**:
   - Detailed error messages for network issues
   - Comprehensive logging for debugging
   - Health check endpoint for connectivity testing

3. **Q&A Feature**:
   - LLM-powered answers about travel destinations
   - Multiple provider support with fallback mechanisms
   - Context-aware responses based on selected route and partner

4. **Robust File Import System**:
   - Multiple fallback paths for module imports
   - Dynamic path resolution for Render environment
   - Improved file permission handling 