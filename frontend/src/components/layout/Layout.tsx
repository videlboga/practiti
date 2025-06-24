import React from 'react';
import { useMediaQuery } from 'react-responsive';
import { Link, Outlet } from 'react-router-dom';
import BottomNavBar from './BottomNavBar';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import HomeIcon from '@mui/icons-material/Home';
import PeopleIcon from '@mui/icons-material/People';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import PersonIcon from '@mui/icons-material/Person';

const navItems = [
  { to: '/', label: 'Главная', icon: <HomeIcon /> },
  { to: '/clients', label: 'Клиенты', icon: <PeopleIcon /> },
  { to: '/bookings', label: 'Занятия', icon: <CalendarMonthIcon /> },
  { to: '/profile', label: 'Профиль', icon: <PersonIcon /> },
];

const Layout: React.FC = () => {
  const isDesktop = useMediaQuery({ minWidth: 1024 });

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default' }}>
      <AppBar position="static" color="secondary" elevation={0} sx={{ borderBottom: '1px solid #e5ded6' }}>
        <Toolbar>
          <Typography variant="h6" color="text.primary" sx={{ fontWeight: 700 }}>
            Пракрити — админ-панель
          </Typography>
        </Toolbar>
      </AppBar>
      <Box sx={{ display: 'flex' }}>
        {isDesktop && (
          <Drawer variant="permanent" open sx={{
            width: 220,
            flexShrink: 0,
            [`& .MuiDrawer-paper`]: { width: 220, boxSizing: 'border-box', bgcolor: 'background.paper', borderRight: '1px solid #e5ded6' },
          }}>
            <Toolbar />
            <List>
              {navItems.map((item) => (
                <ListItem key={item.to} disablePadding>
                  <ListItemButton component={Link} to={item.to}>
                    <ListItemIcon>{item.icon}</ListItemIcon>
                    <ListItemText primary={item.label} />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          </Drawer>
        )}
        <Box component="main" sx={{ flex: 1, p: 3, pb: isDesktop ? 3 : 8, bgcolor: 'background.default', minHeight: '100vh' }}>
          <Toolbar />
          <Outlet />
        </Box>
      </Box>
      {!isDesktop && <BottomNavBar />}
    </Box>
  );
};

export default Layout; 