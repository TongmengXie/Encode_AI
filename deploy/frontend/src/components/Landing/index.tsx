import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Container, 
  Paper, 
  Typography, 
  Button, 
  Box, 
  Grid,
  Card,
  CardContent
} from '@mui/material';
import travelImage from '../../assets/travel.svg';

const Landing: React.FC = () => {
  const navigate = useNavigate();
  const [surveyCompleted, setSurveyCompleted] = useState<boolean>(false);

  // Check if survey is completed on component mount
  useEffect(() => {
    const completed = localStorage.getItem('surveyCompleted') === 'true';
    setSurveyCompleted(completed);
  }, []);

  const handleLaunchSurvey = () => {
    navigate('/survey');
  };

  const handleProceedToNextStep = () => {
    // For now just show an alert
    alert('Embedding calculation would start here!');
  };

  return (
    <Container maxWidth="lg">
      <Paper elevation={3} sx={{ p: 4, mt: 8 }}>
        <Grid container spacing={4}>
          <Grid item xs={12} md={6}>
            <Box sx={{ textAlign: 'center', mb: { xs: 4, md: 0 } }}>
              <Typography variant="h2" component="h1" gutterBottom fontWeight="bold" color="primary">
                WanderMatch
              </Typography>
              <Typography variant="h5" color="text.secondary" paragraph>
                Find your perfect travel companion and plan your next adventure
              </Typography>
              
              <Box mt={6}>
                {!surveyCompleted ? (
                  <Button 
                    variant="contained" 
                    color="primary" 
                    size="large"
                    onClick={handleLaunchSurvey}
                    sx={{ px: 4, py: 1.5, fontSize: '1.1rem' }}
                  >
                    Launch Survey
                  </Button>
                ) : (
                  <Box>
                    <Card sx={{ mb: 3, bgcolor: 'success.light', color: 'white' }}>
                      <CardContent>
                        <Typography variant="h6">
                          Survey Completed!
                        </Typography>
                        <Typography variant="body2">
                          You're ready to proceed to the next step
                        </Typography>
                      </CardContent>
                    </Card>
                    <Button 
                      variant="contained" 
                      color="secondary" 
                      size="large"
                      onClick={handleProceedToNextStep}
                      sx={{ px: 4, py: 1.5, fontSize: '1.1rem' }}
                    >
                      Calculate Travel Match
                    </Button>
                  </Box>
                )}
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box 
              sx={{ 
                height: '400px', 
                backgroundImage: `url(${travelImage})`,
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                borderRadius: 2,
                display: { xs: 'none', md: 'block' }
              }}
            />
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );
};

export default Landing; 