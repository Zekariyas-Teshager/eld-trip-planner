import React, { useState } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  Grid,
  Typography,
  Box,
  Alert,
  CircularProgress
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const getCycleHelperText = (value) => {
  const hours = parseFloat(value) || 0;
  if (hours >= 70) return "❌ Cycle limit reached - 34-hour restart required";
  if (hours >= 60) return "⚠️  Approaching 70-hour limit";
  if (hours >= 50) return "ℹ️  You have good hours remaining";
  return "✅ Plenty of hours available for this trip";
};


const TripPlanner = () => {
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/';
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [formData, setFormData] = useState({
    current_location: '',
    pickup_location: '',
    dropoff_location: '',
    current_cycle_used: ''
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post(`${API_URL}plan-trip/`, {
        ...formData,
        current_cycle_used: parseFloat(formData.current_cycle_used)
      });

      // Navigate to results page with data
      navigate('/results', { state: { tripData: response.data } });
    } catch (err) {
      setError('Failed to plan trip. Please try again.');
      console.error('Error planning trip:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          Trip Planner
        </Typography>
        
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }} align="center">
          Enter your trip details to generate HOS-compliant route and logs
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                required
                fullWidth
                label="Current Location"
                name="current_location"
                value={formData.current_location}
                onChange={handleChange}
                placeholder="e.g., New York, NY"
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                required
                fullWidth
                label="Pickup Location"
                name="pickup_location"
                value={formData.pickup_location}
                onChange={handleChange}
                placeholder="e.g., Chicago, IL"
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                required
                fullWidth
                label="Dropoff Location"
                name="dropoff_location"
                value={formData.dropoff_location}
                onChange={handleChange}
                placeholder="e.g., Los Angeles, CA"
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                required
                fullWidth
                label="Current Cycle Used (Hours)"
                name="current_cycle_used"
                type="number"
                value={formData.current_cycle_used}
                onChange={handleChange}
                placeholder="e.g., 45.5"
                inputProps={{ min: "0", max: "70", step: "0.5" }}
                helperText={getCycleHelperText(formData.current_cycle_used)}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                disabled={loading}
                sx={{ py: 1.5 }}
              >
                {loading ? <CircularProgress size={24} /> : 'Plan Trip'}
              </Button>
            </Grid>
          </Grid>
        </Box>
      </Paper>
    </Container>
  );
};

export default TripPlanner;