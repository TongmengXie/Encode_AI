import React from 'react';
import { Alert, AlertTitle, Box, Button } from '@mui/material';

interface ErrorMessageProps {
  message: string;
  title?: string;
  onRetry?: () => void;
  retryText?: string;
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ 
  message, 
  title = 'Error',
  onRetry,
  retryText = 'Try Again'
}) => {
  return (
    <Box sx={{ mt: 2, mb: 2 }}>
      <Alert 
        severity="error" 
        variant="outlined"
        action={onRetry && (
          <Button 
            color="error" 
            size="small" 
            onClick={onRetry}
          >
            {retryText}
          </Button>
        )}
      >
        {title && <AlertTitle>{title}</AlertTitle>}
        {message}
      </Alert>
    </Box>
  );
};

export default ErrorMessage; 