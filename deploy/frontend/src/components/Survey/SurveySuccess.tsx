import React from 'react';
import { 
  Paper, 
  Typography, 
  Button, 
  Box,
} from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import { SurveySuccessProps } from '../../types';

const SurveySuccess: React.FC<SurveySuccessProps> = ({ onReturnHome }) => {
  return (
    <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
      <Box sx={{ color: 'success.main', fontSize: 60, mb: 2 }}>
        <CheckCircleOutlineIcon fontSize="inherit" />
      </Box>
      
      <Typography variant="h4" gutterBottom>
        Survey Submitted Successfully!
      </Typography>
      
      <Typography variant="body1" paragraph>
        Thank you for completing the travel preferences survey. Your response has been saved.
      </Typography>
      
      <Typography variant="body1" paragraph>
        You can now proceed to the next step of finding your perfect travel match.
      </Typography>
      
      <Button
        variant="contained"
        color="primary"
        size="large"
        onClick={onReturnHome}
        sx={{ mt: 2 }}
      >
        Return to Home
      </Button>
    </Paper>
  );
};

export default SurveySuccess; 