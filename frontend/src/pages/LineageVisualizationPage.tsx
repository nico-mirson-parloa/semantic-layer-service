import React from 'react';
import { Container, Box } from '@mui/material';
import LineageVisualization from '../components/LineageVisualization';

const LineageVisualizationPage: React.FC = () => {
  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <LineageVisualization />
    </Box>
  );
};

export default LineageVisualizationPage;

