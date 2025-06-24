import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    background: { default: '#f9f6f2', paper: '#f5f3ef' },
    primary: { main: '#b89c7d' },
    secondary: { main: '#fff' },
    text: { primary: '#2d1e0f', secondary: '#b89c7d' },
    grey: { 100: '#f5f3ef', 200: '#e5ded6', 300: '#c7b299', 400: '#b89c7d' },
  },
  shape: { borderRadius: 16 },
  typography: {
    fontFamily: 'Montserrat, Arial, sans-serif',
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
}); 