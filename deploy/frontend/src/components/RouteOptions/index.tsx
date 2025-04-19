import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Typography,
  Chip,
  Box,
  LinearProgress,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import FlightIcon from '@mui/icons-material/Flight';
import TrainIcon from '@mui/icons-material/Train';
import DirectionsBusIcon from '@mui/icons-material/DirectionsBus';
import DirectionsCarIcon from '@mui/icons-material/DirectionsCar';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import HighlightOffIcon from '@mui/icons-material/HighlightOff';
import { RouteOption } from '../../types';

interface RouteOptionsProps {
  open: boolean;
  onClose: () => void;
  routes: RouteOption[];
  origin: string;
  destination: string;
  onSelectRoute: (route: RouteOption) => void;
  loading: boolean;
}

const getTransportIcon = (mode: string) => {
  switch (mode.toLowerCase()) {
    case 'flight':
      return <FlightIcon fontSize="large" />;
    case 'train':
      return <TrainIcon fontSize="large" />;
    case 'bus':
      return <DirectionsBusIcon fontSize="large" />;
    case 'car':
      return <DirectionsCarIcon fontSize="large" />;
    default:
      return <DirectionsCarIcon fontSize="large" />;
  }
};

const getCarbonFootprintColor = (footprint: string) => {
  const level = footprint.toLowerCase();
  if (level.includes('low')) return 'success';
  if (level.includes('medium')) return 'warning';
  if (level.includes('high')) return 'error';
  return 'default';
};

const RouteOptions: React.FC<RouteOptionsProps> = ({
  open,
  onClose,
  routes,
  origin,
  destination,
  onSelectRoute,
  loading
}) => {
  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      fullWidth
      maxWidth="md"
      scroll="paper"
    >
      <DialogTitle>
        <Typography variant="h5" fontWeight="bold">
          Transportation Options: {origin} to {destination}
        </Typography>
        {loading && <LinearProgress sx={{ mt: 2 }} />}
      </DialogTitle>
      
      <DialogContent dividers>
        {loading ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="body1">
              Generating route options...
            </Typography>
          </Box>
        ) : (
          <Grid container spacing={3}>
            {routes.map((route, index) => (
              <Grid item xs={12} md={6} key={index}>
                <Card 
                  elevation={3}
                  sx={{ 
                    height: '100%', 
                    display: 'flex', 
                    flexDirection: 'column',
                    transition: 'transform 0.2s',
                    '&:hover': {
                      transform: 'scale(1.02)'
                    }
                  }}
                >
                  <CardContent sx={{ flexGrow: 1 }}>
                    <Box 
                      sx={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        mb: 2,
                        pb: 1,
                        borderBottom: '1px solid #eee'
                      }}
                    >
                      <Box sx={{ mr: 2 }}>
                        {getTransportIcon(route.mode)}
                      </Box>
                      <Typography variant="h6" component="div">
                        {route.mode.charAt(0).toUpperCase() + route.mode.slice(1)}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Duration
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {route.duration}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Cost
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {route.cost}
                      </Typography>
                    </Box>
                    
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Carbon Footprint
                      </Typography>
                      <Chip 
                        label={route.carbon_footprint} 
                        color={getCarbonFootprintColor(route.carbon_footprint)}
                        size="small"
                      />
                    </Box>
                    
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="body2" color="text.secondary">
                        Comfort Level
                      </Typography>
                      <Typography variant="body1">
                        {route.comfort_level}
                      </Typography>
                    </Box>
                    
                    <Divider sx={{ my: 2 }} />
                    
                    <Box>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Pros & Cons
                      </Typography>
                      
                      <List dense>
                        {route.pros.map((pro, i) => (
                          <ListItem key={`pro-${i}`} disableGutters>
                            <ListItemIcon sx={{ minWidth: 32 }}>
                              <CheckCircleOutlineIcon color="success" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary={pro} />
                          </ListItem>
                        ))}
                        
                        {route.cons.map((con, i) => (
                          <ListItem key={`con-${i}`} disableGutters>
                            <ListItemIcon sx={{ minWidth: 32 }}>
                              <HighlightOffIcon color="error" fontSize="small" />
                            </ListItemIcon>
                            <ListItemText primary={con} />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  </CardContent>
                  
                  <CardActions>
                    <Button 
                      size="large" 
                      variant="contained" 
                      fullWidth
                      onClick={() => onSelectRoute(route)}
                    >
                      Select {route.mode}
                    </Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
            
            {routes.length === 0 && !loading && (
              <Grid item xs={12}>
                <Box sx={{ p: 4, textAlign: 'center' }}>
                  <Typography variant="body1">
                    No route options found. Please try a different origin or destination.
                  </Typography>
                </Box>
              </Grid>
            )}
          </Grid>
        )}
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
      </DialogActions>
    </Dialog>
  );
};

export default RouteOptions; 