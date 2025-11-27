// src/components/TripResults.js
import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Chip,
  Alert
} from '@mui/material';
import {
  ArrowBack,
  Map as MapIcon,
  Assignment,
  Description,
  Download,
  PictureAsPdf
} from '@mui/icons-material';
import RouteMap from './RouteMap';
import PDFViewer from './PDFViewer';

// MapSection Component
const MapSection = ({ stops, routeCoordinates }) => (
  <Card elevation={3} sx={{ mt: 3 }}>
    <CardContent>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <MapIcon sx={{ mr: 1 }} />
        <Typography variant="h6" component="h2">
          Interactive Route Map
        </Typography>
      </Box>

      {routeCoordinates && routeCoordinates.length > 0 ? (
        <Box>
          <RouteMap
            stops={stops}
            routeCoordinates={routeCoordinates}
          />
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1, textAlign: 'center' }} component="div">
            🗺️ Interactive map showing your route with all stops. Zoom, pan, and click markers for details.
          </Typography>
        </Box>
      ) : (
        <Alert severity="info">
          <Typography variant="body2" component="div">
            Map data is being calculated...
            {stops && stops.length > 0 && (
              <span> Your route has {stops.length} stops planned.</span>
            )}
          </Typography>
        </Alert>
      )}
    </CardContent>
  </Card>
);

const TripResults = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const tripData = location.state?.tripData;
  const [selectedPdf, setSelectedPdf] = useState(null);
  const [pdfViewerOpen, setPdfViewerOpen] = useState(false);

  const handleViewPdf = (pdfInfo) => {
    setSelectedPdf(pdfInfo);
    setPdfViewerOpen(true);
  };

  const handleClosePdf = () => {
    setPdfViewerOpen(false);
    setSelectedPdf(null);
  };

  // PDF Section Component
  const handleDownloadPdf = (pdfUrl, filename) => {
    if (!pdfUrl) {
      console.error('No PDF URL available');
      return;
    }

    // Create a temporary anchor element to trigger download
    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = filename;
    link.target = '_blank'; // Open in new tab for safety
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // PDF Section Component - UPDATED FOR URLS
  const PDFSection = ({ pdfLogs }) => (
    <Card elevation={3} sx={{ mt: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Description sx={{ mr: 1 }} />
          <Typography variant="h6" component="h2">
            FMCSA Daily Log Sheets
          </Typography>
        </Box>

        {pdfLogs && pdfLogs.length > 0 ? (
          <List>
            {pdfLogs.map((log, index) => (
              <ListItem key={index} divider>
                <ListItemText
                  primary={
                    <Typography variant="h6" color="primary" component="div">
                      📋 Day {log.day_number} - FMCSA Log Sheet
                      {log.requires_restart && (
                        <Chip 
                          label="34-hr Restart Required" 
                          color="warning" 
                          size="small" 
                          sx={{ ml: 1 }}
                        />
                      )}
                    </Typography>
                  }
                  secondary={
                    <Grid container spacing={1} sx={{ mt: 1 }}>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" component="div">
                          🚗 Driving: {log.driving_hours}h
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" component="div">
                          💼 On Duty: {log.on_duty_hours}h
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" component="div">
                          🏠 Off Duty: {log.off_duty_hours}h
                        </Typography>
                      </Grid>
                      <Grid item xs={6} sm={3}>
                        <Typography variant="body2" component="div">
                          📊 Cycle: {log.cycle_used}/70h
                        </Typography>
                      </Grid>
                      {log.pdf_url && (
                        <Grid item xs={12}>
                          <Typography variant="caption" color="text.secondary" component="div">
                            URL: {log.pdf_url}
                          </Typography>
                        </Grid>
                      )}
                    </Grid>
                  }
                />
                <Box sx={{ display: 'flex', gap: 1, flexDirection: { xs: 'column', sm: 'row' } }}>
                  {log.pdf_url ? (
                    <>
                      <Button
                        variant="contained"
                        size="small"
                        onClick={() => handleViewPdf({
                          ...log,
                          pdf_url: log.pdf_url,
                          filename: log.filename
                        })}
                        startIcon={<PictureAsPdf />}
                      >
                        View
                      </Button>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => handleDownloadPdf(log.pdf_url, log.filename)}
                        startIcon={<Download />}
                      >
                        Download
                      </Button>
                    </>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      PDF Not Available
                    </Typography>
                  )}
                </Box>
              </ListItem>
            ))}
          </List>
        ) : (
          <Alert severity="info">
            <Typography>
              No PDF logs generated. Please check if the backend PDF service is working.
            </Typography>
          </Alert>
        )}
      </CardContent>
    </Card>
  );

  if (!tripData) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h5" color="error" component="h1">
            No trip data found
          </Typography>
          <Button
            variant="contained"
            sx={{ mt: 2 }}
            onClick={() => navigate('/')}
          >
            Plan New Trip
          </Button>
        </Paper>
      </Container>
    );
  }

  const getStopColor = (type) => {
    const colors = {
      'PICKUP': 'primary',
      'DROPOFF': 'secondary',
      'FUEL': 'warning',
      'REST': 'success',
      'OVERNIGHT': 'info'
    };
    return colors[type] || 'default';
  };

  const getStopIcon = (type) => {
    const icons = {
      'PICKUP': '📦',
      'DROPOFF': '🏁',
      'FUEL': '⛽',
      'REST': '🛌',
      'OVERNIGHT': '🌙'
    };
    return icons[type] || '📍';
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Button
          startIcon={<ArrowBack />}
          onClick={() => navigate('/')}
          sx={{ mb: 2 }}
        >
          Back to Planner
        </Button>

        <Typography variant="h4" component="h1" gutterBottom>
          Trip Plan Results
        </Typography>
        <Typography variant="body1" color="text.secondary" component="div">
          Your HOS-compliant route has been calculated successfully
        </Typography>
      </Box>

      {/* Main Content Grid */}
      <Grid container spacing={3}>
        {/* Trip Summary */}
        <Grid size={12}>
          <Card elevation={3}>
            <CardContent>
              <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }} component="h2">
                📊 Trip Summary
              </Typography>
              <Grid container spacing={2}>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Typography variant="body2" color="text.secondary" component="div">
                    Total Distance
                  </Typography>
                  <Typography variant="h6" color="primary" component="div">
                    {tripData.total_distance_km} km
                    <Typography variant="body2" color="text.secondary" component="div">
                      ({(tripData.total_distance_km * 0.621371).toFixed(0)} miles)
                    </Typography>
                  </Typography>
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Typography variant="body2" color="text.secondary" component="div">
                    Total Duration
                  </Typography>
                  <Typography variant="h6" color="primary" component="div">
                    {tripData.total_duration_hours} hours
                  </Typography>
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Typography variant="body2" color="text.secondary" component="div">
                    Number of Stops
                  </Typography>
                  <Typography variant="h6" color="primary" component="div">
                    {tripData.stops.length}
                  </Typography>
                </Grid>
                <Grid size={{ xs: 12, sm: 6, md: 3 }}>
                  <Typography variant="body2" color="text.secondary" component="div">
                    Days Required
                  </Typography>
                  <Typography variant="h6" color="primary" component="div">
                    {tripData.daily_logs.length}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Route Stops */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card elevation={3} sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <MapIcon sx={{ mr: 1 }} />
                <Typography variant="h6" component="h2">
                  Route Stops & Schedule
                </Typography>
              </Box>
              <List sx={{ maxHeight: '400px', overflow: 'auto' }}>
                {tripData.stops.map((stop, index) => (
                  <ListItem key={index} divider>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <span style={{ fontSize: '1.2em' }}>{getStopIcon(stop.type)}</span>
                          <Chip
                            label={stop.type}
                            color={getStopColor(stop.type)}
                            size="small"
                          />
                          <Typography variant="subtitle1" sx={{ flex: 1 }} component="div">
                            {stop.location}
                          </Typography>
                        </Box>
                      }
                      secondary={
                        // Use fragment with span elements
                        <>
                          <Typography variant="body2" component="span" sx={{ display: 'block' }}>
                            📍 Distance: {stop.distance} km
                          </Typography>
                          <Typography variant="body2" component="span" sx={{ display: 'block' }}>
                            ⏱️ Duration: {stop.duration.toFixed(1)} hours
                          </Typography>
                          <Typography variant="body2" component="span" sx={{ display: 'block' }}>
                            🕒 Stop time: {stop.stop_duration} hours
                          </Typography>
                        </>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Daily Logs */}
        <Grid size={{ xs: 12, md: 6 }}>
          <Card elevation={3} sx={{ height: '100%' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Assignment sx={{ mr: 1 }} />
                <Typography variant="h6" component="h2">
                  HOS Compliance Logs
                </Typography>
              </Box>
              <List sx={{ maxHeight: '400px', overflow: 'auto' }}>
                {tripData.daily_logs.map((log, index) => (
                  <ListItem key={index} divider>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Typography variant="subtitle1" fontWeight="bold" component="div">
                            📅 Day {log.day_number}
                          </Typography>
                          {log.requires_34_hour_restart && (
                            <Chip
                              label="34-hr restart needed"
                              color="warning"
                              size="small"
                            />
                          )}
                        </Box>
                      }
                      secondary={
                        // Use fragment with span elements
                        <>
                          <Grid container spacing={1} sx={{ mt: 1 }}>
                            <Grid size={6}>
                              <Typography variant="body2" component="span">
                                🚗 Driving: {log.driving_hours}h
                              </Typography>
                            </Grid>
                            <Grid size={6}>
                              <Typography variant="body2" component="span">
                                💼 On Duty: {log.on_duty_hours}h
                              </Typography>
                            </Grid>
                            <Grid size={6}>
                              <Typography variant="body2" component="span">
                                🏠 Off Duty: {log.off_duty_hours}h
                              </Typography>
                            </Grid>
                            <Grid size={6}>
                              <Typography variant="body2" component="span">
                                📊 Cycle: {log.cycle_used}/70h
                              </Typography>
                            </Grid>
                          </Grid>
                        </>
                      }
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Map Section */}
      <MapSection
        stops={tripData.stops}
        routeCoordinates={tripData.route_coordinates}
      />

      {/* PDF Section */}
      <PDFSection pdfLogs={tripData.fmcsa_daily_logs} />

      {/* PDF Viewer Modal */}
      <PDFViewer
        open={pdfViewerOpen}
        onClose={handleClosePdf}
        pdfUrl={selectedPdf?.pdf_url}
        dayNumber={selectedPdf?.day_number}
        filename={selectedPdf?.filename}
      />

      {/* Action Buttons */}
      <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'center' }}>
        <Button
          variant="outlined"
          onClick={() => navigate('/')}
        >
          Plan Another Trip
        </Button>
        <Button
          variant="contained"
          onClick={() => window.print()}
        >
          Print This Plan
        </Button>
      </Box>
    </Container>
  );
};

export default TripResults;