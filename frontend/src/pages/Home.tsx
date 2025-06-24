import React from 'react';
import { useDashboardMetrics } from '../hooks/useClients';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import CircularProgress from '@mui/material/CircularProgress';

const metricStyle = {
  minWidth: 180,
  minHeight: 100,
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  borderRadius: 16,
  boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
  background: '#fff',
};

const Home: React.FC = () => {
  const { data, isLoading, error } = useDashboardMetrics();

  return (
    <Stack spacing={4} sx={{ p: 3 }}>
      <Typography variant="h5" fontWeight={700} mb={2}>
        Дашборд
      </Typography>
      {isLoading && <CircularProgress />}
      {error && (
        <Typography color="error">
          Ошибка загрузки метрик{error instanceof Error ? `: ${error.message}` : ''}
        </Typography>
      )}
      {!isLoading && !error && !data && (
        <Typography color="text.secondary">Нет доступных метрик</Typography>
      )}
      {data && (
        <>
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
            <Card sx={metricStyle}>
              <CardContent>
                <Typography variant="h6">Клиентов всего</Typography>
                <Typography variant="h4" fontWeight={700}>{data.totalClients}</Typography>
              </CardContent>
            </Card>
            <Card sx={metricStyle}>
              <CardContent>
                <Typography variant="h6">Активных клиентов</Typography>
                <Typography variant="h4" fontWeight={700}>{data.activeClients}</Typography>
              </CardContent>
            </Card>
            <Card sx={metricStyle}>
              <CardContent>
                <Typography variant="h6">Абонементов всего</Typography>
                <Typography variant="h4" fontWeight={700}>{data.totalSubscriptions}</Typography>
              </CardContent>
            </Card>
            <Card sx={metricStyle}>
              <CardContent>
                <Typography variant="h6">Активных абонементов</Typography>
                <Typography variant="h4" fontWeight={700}>{data.activeSubscriptions}</Typography>
              </CardContent>
            </Card>
          </Stack>
          <Stack mt={4}>
            <Card sx={{ ...metricStyle, minWidth: 320 }}>
              <CardContent>
                <Typography variant="h6">Посещений за месяц</Typography>
                <Typography variant="h4" fontWeight={700}>{data.bookingsThisMonth}</Typography>
                {/* Здесь может быть график посещений (заглушка) */}
                <div style={{ height: 120, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#bdbdbd' }}>
                  <span>График посещаемости (скоро)</span>
                </div>
              </CardContent>
            </Card>
          </Stack>
        </>
      )}
    </Stack>
  );
};

export default Home; 