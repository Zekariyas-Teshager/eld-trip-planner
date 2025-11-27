import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Stack
} from '@mui/material';
import {
  Close,
  Download,
  PictureAsPdf,
  Description,
  Print,
  Share
} from '@mui/icons-material';

const PDFViewer = ({ open, onClose, pdfUrl, dayNumber, logData }) => {
  const handleDownload = () => {
    if (!pdfUrl) return;

    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = `fmcsa_log_day_${dayNumber}.pdf`;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handlePrint = () => {
    if (!pdfUrl) return;
    window.open(pdfUrl, '_blank');
  };

  // Mock log data for preview
  const mockLogData = logData || {
    driving_hours: 11,
    on_duty_hours: 13,
    off_duty_hours: 11,
    cycle_used: 56.5,
    requires_34_hour_restart: false
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center">
            <PictureAsPdf sx={{ mr: 1, color: 'red' }} />
            <Typography variant="h6">
              FMCSA Daily Log - Day {dayNumber}
            </Typography>
          </Box>
          <IconButton onClick={onClose}>
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        <Stack spacing={3}>
          {/* Preview Card */}
          <Card variant="outlined">
            <CardContent>
              <Box textAlign="center" sx={{ mb: 3 }}>
                <Description sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
                <Typography variant="h5" gutterBottom>
                  FMCSA Daily Log Sheet
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Day {dayNumber} - Ready for Download
                </Typography>
              </Box>

              {/* Log Summary */}
              <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  📊 Log Summary
                </Typography>
                <Stack spacing={1}>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2">Driving Hours:</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {mockLogData.driving_hours}h
                    </Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2">On Duty Hours:</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {mockLogData.on_duty_hours}h
                    </Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2">Off Duty Hours:</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {mockLogData.off_duty_hours}h
                    </Typography>
                  </Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="body2">Cycle Used:</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {mockLogData.cycle_used}/70h
                    </Typography>
                  </Box>
                  {mockLogData.requires_34_hour_restart && (
                    <Box display="flex" justifyContent="space-between" sx={{ color: 'warning.main' }}>
                      <Typography variant="body2">Status:</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        34-hour Restart Required
                      </Typography>
                    </Box>
                  )}
                </Stack>
              </Box>

              {/* Features List */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  ✅ This log sheet includes:
                </Typography>
                <Stack spacing={0.5}>
                  <Typography variant="body2">• 24-hour grid with proper duty status</Typography>
                  <Typography variant="body2">• FMCSA-compliant format</Typography>
                  <Typography variant="body2">• Carrier and driver information</Typography>
                  <Typography variant="body2">• Location remarks for each duty change</Typography>
                  <Typography variant="body2">• Total miles and hours calculation</Typography>
                  <Typography variant="body2">• Driver certification signature line</Typography>
                </Stack>
              </Box>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <Box display="flex" gap={2} justifyContent="center" flexWrap="wrap">
            <Button
              variant="contained"
              startIcon={<Download />}
              onClick={handleDownload}
              size="large"
              disabled={!pdfUrl}
            >
              Download PDF
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<Print />}
              onClick={handlePrint}
              size="large"
              disabled={!pdfUrl}
            >
              Open for Printing
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<Share />}
              onClick={() => {
                if (pdfUrl) {
                  navigator.clipboard.writeText(pdfUrl);
                  // You could add a snackbar notification here
                  alert('PDF link copied to clipboard!');
                }
              }}
              size="large"
              disabled={!pdfUrl}
            >
              Copy Link
            </Button>
          </Box>

          {/* Help Text */}
          <Box textAlign="center">
            <Typography variant="body2" color="text.secondary">
              💡 <strong>Pro Tip:</strong> Print this log and keep it in your vehicle for 8 days as required by FMCSA regulations.
            </Typography>
          </Box>

          {/* Development Note */}
          {!pdfUrl && (
            <Card sx={{ bgcolor: 'info.50', borderColor: 'info.main' }}>
              <CardContent>
                <Typography variant="body2" color="info.main">
                  <strong>Development Note:</strong> In the production version, this will generate 
                  and display actual FMCSA-compliant PDF log sheets. For now, you can see the 
                  calculated HOS compliance data above.
                </Typography>
              </CardContent>
            </Card>
          )}
        </Stack>
      </DialogContent>
    </Dialog>
  );
};

export default PDFViewer;