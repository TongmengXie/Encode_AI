import React from 'react';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import { 
  TextField,
  Button,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
  Typography,
  Box,
  Paper
} from '@mui/material';
import { SurveyFormProps, SurveyFormData } from '../../types';

// Define survey field validation schema
const SurveySchema = Yup.object().shape({
  real_name: Yup.string().required('Name is required'),
  age_group: Yup.string().required('Age group is required'),
  gender: Yup.string(),
  nationality: Yup.string(),
  travel_budget: Yup.string().required('Budget is required'),
  travel_season: Yup.string().required('Preferred season is required'),
  interests: Yup.string(),
  travel_style: Yup.string().required('Travel style is required'),
  accommodation_preference: Yup.string()
});

const SurveyForm: React.FC<SurveyFormProps> = ({ onSubmit, isSubmitting }) => {
  const initialValues: SurveyFormData = {
    real_name: '',
    age_group: '',
    gender: '',
    nationality: '',
    travel_budget: '',
    travel_season: '',
    interests: '',
    travel_style: '',
    accommodation_preference: ''
  };

  const formik = useFormik({
    initialValues,
    validationSchema: SurveySchema,
    onSubmit: (values) => {
      onSubmit(values);
    },
  });

  return (
    <Paper elevation={3} sx={{ p: 4 }}>
      <Typography variant="h4" gutterBottom color="primary" fontWeight="medium">
        Travel Preferences Survey
      </Typography>
      <Typography variant="body1" paragraph color="text.secondary" mb={4}>
        Tell us about yourself and your travel preferences to find your perfect travel companion.
      </Typography>
      
      <form onSubmit={formik.handleSubmit}>
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              id="real_name"
              name="real_name"
              label="Your Name"
              value={formik.values.real_name}
              onChange={formik.handleChange}
              error={formik.touched.real_name && Boolean(formik.errors.real_name)}
              helperText={formik.touched.real_name && formik.errors.real_name}
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControl 
              fullWidth 
              error={formik.touched.age_group && Boolean(formik.errors.age_group)}
            >
              <InputLabel>Age Group</InputLabel>
              <Select
                id="age_group"
                name="age_group"
                value={formik.values.age_group}
                onChange={formik.handleChange}
                label="Age Group"
              >
                <MenuItem value="18–24">18–24</MenuItem>
                <MenuItem value="25–34">25–34</MenuItem>
                <MenuItem value="35–44">35–44</MenuItem>
                <MenuItem value="45–54">45–54</MenuItem>
                <MenuItem value="55–64">55–64</MenuItem>
                <MenuItem value="65+">65+</MenuItem>
              </Select>
              {formik.touched.age_group && formik.errors.age_group && (
                <FormHelperText>{formik.errors.age_group}</FormHelperText>
              )}
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Gender</InputLabel>
              <Select
                id="gender"
                name="gender"
                value={formik.values.gender}
                onChange={formik.handleChange}
                label="Gender"
              >
                <MenuItem value="Male">Male</MenuItem>
                <MenuItem value="Female">Female</MenuItem>
                <MenuItem value="Non-binary">Non-binary</MenuItem>
                <MenuItem value="Prefer not to say">Prefer not to say</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              id="nationality"
              name="nationality"
              label="Nationality"
              value={formik.values.nationality}
              onChange={formik.handleChange}
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControl 
              fullWidth 
              error={formik.touched.travel_budget && Boolean(formik.errors.travel_budget)}
            >
              <InputLabel>Travel Budget</InputLabel>
              <Select
                id="travel_budget"
                name="travel_budget"
                value={formik.values.travel_budget}
                onChange={formik.handleChange}
                label="Travel Budget"
              >
                <MenuItem value="$500">Under $500</MenuItem>
                <MenuItem value="$1000">$500 - $1000</MenuItem>
                <MenuItem value="$2000">$1000 - $2000</MenuItem>
                <MenuItem value="$3000">$2000 - $3000</MenuItem>
                <MenuItem value="$5000">$3000 - $5000</MenuItem>
                <MenuItem value="$5000+">$5000+</MenuItem>
              </Select>
              {formik.touched.travel_budget && formik.errors.travel_budget && (
                <FormHelperText>{formik.errors.travel_budget}</FormHelperText>
              )}
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControl 
              fullWidth 
              error={formik.touched.travel_season && Boolean(formik.errors.travel_season)}
            >
              <InputLabel>Preferred Travel Season</InputLabel>
              <Select
                id="travel_season"
                name="travel_season"
                value={formik.values.travel_season}
                onChange={formik.handleChange}
                label="Preferred Travel Season"
              >
                <MenuItem value="Spring">Spring</MenuItem>
                <MenuItem value="Summer">Summer</MenuItem>
                <MenuItem value="Fall">Fall</MenuItem>
                <MenuItem value="Winter">Winter</MenuItem>
                <MenuItem value="Any">Any time of year</MenuItem>
              </Select>
              {formik.touched.travel_season && formik.errors.travel_season && (
                <FormHelperText>{formik.errors.travel_season}</FormHelperText>
              )}
            </FormControl>
          </Grid>
          
          <Grid item xs={12}>
            <TextField
              fullWidth
              id="interests"
              name="interests"
              label="Travel Interests (e.g., hiking, cuisine, history)"
              value={formik.values.interests}
              onChange={formik.handleChange}
              multiline
              rows={2}
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControl 
              fullWidth 
              error={formik.touched.travel_style && Boolean(formik.errors.travel_style)}
            >
              <InputLabel>Travel Style</InputLabel>
              <Select
                id="travel_style"
                name="travel_style"
                value={formik.values.travel_style}
                onChange={formik.handleChange}
                label="Travel Style"
              >
                <MenuItem value="Luxury">Luxury</MenuItem>
                <MenuItem value="Comfort">Comfort-focused</MenuItem>
                <MenuItem value="Budget">Budget-conscious</MenuItem>
                <MenuItem value="Adventure">Adventure</MenuItem>
                <MenuItem value="Cultural">Cultural immersion</MenuItem>
                <MenuItem value="Mix of planned and spontaneous">Mix of planned and spontaneous</MenuItem>
              </Select>
              {formik.touched.travel_style && formik.errors.travel_style && (
                <FormHelperText>{formik.errors.travel_style}</FormHelperText>
              )}
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Accommodation Preference</InputLabel>
              <Select
                id="accommodation_preference"
                name="accommodation_preference"
                value={formik.values.accommodation_preference}
                onChange={formik.handleChange}
                label="Accommodation Preference"
              >
                <MenuItem value="Luxury hotel">Luxury hotel</MenuItem>
                <MenuItem value="Mid-range hotel">Mid-range hotel</MenuItem>
                <MenuItem value="Budget hotel">Budget hotel</MenuItem>
                <MenuItem value="Hostel">Hostel</MenuItem>
                <MenuItem value="Vacation rental">Vacation rental</MenuItem>
                <MenuItem value="Homestay">Homestay</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12}>
            <Box mt={3} display="flex" justifyContent="center">
              <Button
                type="submit"
                variant="contained"
                color="primary"
                size="large"
                disabled={isSubmitting}
                sx={{ px: 4, py: 1.5, fontSize: '1.1rem' }}
              >
                {isSubmitting ? 'Submitting...' : 'Submit Survey'}
              </Button>
            </Box>
          </Grid>
        </Grid>
      </form>
    </Paper>
  );
};

export default SurveyForm; 