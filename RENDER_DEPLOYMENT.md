# WanderMatch Render Deployment Checklist

Follow these steps to deploy WanderMatch to Render:

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