import React from 'react';
import { AppBar, Toolbar, Typography, Container } from '@mui/material';
import DirectionsCarIcon from '@mui/icons-material/DirectionsCar';

const Header = () => {
  return (
    <AppBar position="static">
      <Container maxWidth="lg">
        <Toolbar>
          <DirectionsCarIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            ELD Trip Planner
          </Typography>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default Header;