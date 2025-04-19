import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, Box, Alert, CircularProgress } from '@mui/material';
import SurveyForm from './SurveyForm';
import SurveySuccess from './SurveySuccess';
import { SurveyFormData } from '../../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Survey: React.FC = () => {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [isSubmitted, setIsSubmitted] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (values: SurveyFormData) => {
    setIsSubmitting(true);
    setError(null);
    
    try {
      // Send the survey data to the API
      const response = await fetch(`${API_URL}/api/survey`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(values),
      });
      
      const data = await response.json();
      
      if (data.success) {
        setIsSubmitted(true);
        // Mark survey as completed in local storage
        localStorage.setItem('surveyCompleted', 'true');
      } else {
        setError(data.message || 'Failed to save survey data. Please try again.');
      }
    } catch (err) {
      setError('An error occurred while submitting the survey. Please try again later.');
      console.error('Survey submission error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReturnHome = () => {
    navigate('/');
  };

  return (
    <Container maxWidth="md">
      <Box mt={5} mb={5}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}
        
        {isSubmitting && (
          <Box display="flex" justifyContent="center" my={4}>
            <CircularProgress />
          </Box>
        )}
        
        {isSubmitted ? (
          <SurveySuccess onReturnHome={handleReturnHome} />
        ) : (
          <SurveyForm 
            onSubmit={handleSubmit} 
            isSubmitting={isSubmitting} 
          />
        )}
      </Box>
    </Container>
  );
};

export default Survey; 