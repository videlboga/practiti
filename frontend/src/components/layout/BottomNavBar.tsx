import React from 'react';
import BottomNavigation from '@mui/material/BottomNavigation';
import BottomNavigationAction from '@mui/material/BottomNavigationAction';
import HomeIcon from '@mui/icons-material/Home';
import PeopleIcon from '@mui/icons-material/People';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import PersonIcon from '@mui/icons-material/Person';
import Paper from '@mui/material/Paper';
import { useLocation, useNavigate } from 'react-router-dom';

const navItems = [
  { label: 'Главная', icon: <HomeIcon />, path: '/' },
  { label: 'Клиенты', icon: <PeopleIcon />, path: '/clients' },
  { label: 'Занятия', icon: <CalendarMonthIcon />, path: '/bookings' },
  { label: 'Профиль', icon: <PersonIcon />, path: '/profile' },
];

const BottomNavBar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const value = navItems.findIndex(item => location.pathname.startsWith(item.path));

  return (
    <Paper sx={{ position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 100 }} elevation={3}>
      <BottomNavigation
        showLabels
        value={value === -1 ? 0 : value}
        onChange={(_, newValue) => navigate(navItems[newValue].path)}
        sx={{ bgcolor: 'background.paper', borderTop: '1px solid #e5ded6' }}
      >
        {navItems.map((item) => (
          <BottomNavigationAction
            key={item.label}
            label={item.label}
            icon={item.icon}
            sx={{
              color: value === navItems.findIndex(i => i.label === item.label) ? 'primary.main' : 'grey.400',
              '&.Mui-selected': { color: 'primary.main' },
            }}
          />
        ))}
      </BottomNavigation>
    </Paper>
  );
};

export default BottomNavBar; 