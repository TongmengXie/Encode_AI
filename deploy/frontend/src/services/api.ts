import { RouteOption } from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

/**
 * Submit survey data to the backend
 */
export const submitSurvey = async (surveyData: any) => {
  try {
    const response = await fetch(`${API_URL}/api/survey`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(surveyData),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error submitting survey:', error);
    throw error;
  }
};

/**
 * Trigger embedding calculation and get partner matches
 */
export const calculateEmbedding = async () => {
  try {
    const response = await fetch(`${API_URL}/api/embedding`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error calculating embedding:', error);
    throw error;
  }
};

/**
 * Generate route options between origin and destination
 */
export const generateRoutes = async (origin: string, destination: string) => {
  try {
    const response = await fetch(`${API_URL}/api/generate-routes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ origin, destination }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error generating routes:', error);
    throw error;
  }
};

/**
 * Save the selected route option
 */
export const selectRoute = async (selectedRoute: RouteOption) => {
  try {
    const response = await fetch(`${API_URL}/api/select-route`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ selected_route: selectedRoute }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error selecting route:', error);
    throw error;
  }
}; 