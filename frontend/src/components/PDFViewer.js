// src/components/PDFViewer.js
import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Box,
  Typography,
  Button,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Close,
  Download,
  PictureAsPdf
} from '@mui/icons-material';

const PDFViewer = ({ open, onClose, pdfUrl, dayNumber, filename }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const handleDownload = () => {
    if (!pdfUrl) return;

    // Create a temporary anchor element to trigger download
    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = filename || `fmcsa_log_day_${dayNumber}.pdf`;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleLoad = () => {
    setLoading(false);
    setError(null);
  };

  const handleError = () => {
    setLoading(false);
    setError('Failed to load PDF. You can still download it using the button below.');
  };

  // Reset state when modal opens/closes
  React.useEffect(() => {
    if (open) {
      setLoading(true);
      setError(null);
    }
  }, [open, pdfUrl]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center">
            <PictureAsPdf sx={{ mr: 1, color: 'red' }} />
            <Typography variant="h6">
              FMCSA Daily Log - Day {dayNumber}
            </Typography>
          </Box>
          <Box>
            <Button
              startIcon={<Download />}
              onClick={handleDownload}
              variant="outlined"
              size="small"
              sx={{ mr: 1 }}
              disabled={!pdfUrl}
            >
              Download
            </Button>
            <IconButton onClick={onClose}>
              <Close />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        <Box sx={{ height: '100%', width: '100%', display: 'flex', justifyContent: 'center', flexDirection: 'column' }}>
          {loading && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <CircularProgress sx={{ mb: 2 }} />
              <Typography>Loading PDF...</Typography>
            </Box>
          )}
          
          {error && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {!pdfUrl ? (
            <Alert severity="error">
              PDF URL not available. Please try generating the trip plan again.
            </Alert>
          ) : (
            <Box sx={{ flex: 1, minHeight: '600px' }}>
              <iframe
                src={pdfUrl}
                width="100%"
                height="600px"
                style={{ 
                  border: 'none',
                  display: loading ? 'none' : 'block'
                }}
                onLoad={handleLoad}
                onError={handleError}
                title={`FMCSA Log Day ${dayNumber}`}
              />
              
              {/* Fallback for iframe issues */}
              <Box sx={{ mt: 2, textAlign: 'center' }}>
                <Typography variant="body2" color="text.secondary">
                  Can't view the PDF?{' '}
                  <Button 
                    variant="text" 
                    size="small" 
                    onClick={() => window.open(pdfUrl, '_blank')}
                  >
                    Open in new tab
                  </Button>
                </Typography>
              </Box>
            </Box>
          )}
        </Box>
      </DialogContent>
    </Dialog>
  );
};

export default PDFViewer;