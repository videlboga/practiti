import React from 'react';
import { useClients } from '../hooks/useClients';
import { useQuery } from '@tanstack/react-query';
import { getSubscriptions } from '../services/apiClient';
import { Client } from '../types/client';
import { Subscription } from '../types/subscription';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Paper from '@mui/material/Paper';

function exportToCSV(rows: any[], filename: string) {
  const csv = [Object.keys(rows[0]).join(','), ...rows.map(r => Object.values(r).join(','))].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
}

const Reports: React.FC = () => {
  const [search, setSearch] = React.useState('');
  const [status, setStatus] = React.useState('');
  const [type, setType] = React.useState('');
  const { data: clientsData } = useClients(1, 1000, { search, status });
  const { data: subscriptions = [] } = useQuery(['subscriptions'], getSubscriptions);

  // Фильтрация абонементов по типу
  const filteredSubs = subscriptions.filter(s => (type ? s.type === type : true));

  // Объединяем данные для отчёта
  const rows = filteredSubs.map(sub => {
    const client = clientsData?.data.find(c => c.id === sub.client_id);
    return {
      'Имя клиента': client?.name || '',
      'Телефон': client?.phone || '',
      'Тип абонемента': sub.type,
      'Статус': sub.status,
      'Дата начала': sub.start_date,
      'Дата окончания': sub.end_date,
      'Осталось занятий': sub.remaining_classes,
    };
  });

  return (
    <Stack spacing={3} sx={{ p: 3 }}>
      <Typography variant="h5" fontWeight={700} mb={2}>
        Отчёты и экспорт
      </Typography>
      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
        <TextField label="Поиск клиента" value={search} onChange={e => setSearch(e.target.value)} />
        <Select value={status} onChange={e => setStatus(e.target.value)} displayEmpty sx={{ minWidth: 160 }}>
          <MenuItem value="">Все статусы</MenuItem>
          <MenuItem value="active">Активные</MenuItem>
          <MenuItem value="inactive">Неактивные</MenuItem>
        </Select>
        <Select value={type} onChange={e => setType(e.target.value)} displayEmpty sx={{ minWidth: 160 }}>
          <MenuItem value="">Все типы</MenuItem>
          <MenuItem value="trial">Пробное</MenuItem>
          <MenuItem value="single">Разовое</MenuItem>
          <MenuItem value="newbie4">Новичок (4)</MenuItem>
          <MenuItem value="regular4">4 занятия</MenuItem>
          <MenuItem value="regular8">8 занятий</MenuItem>
          <MenuItem value="regular12">12 занятий</MenuItem>
          <MenuItem value="unlimited">Безлимит</MenuItem>
        </Select>
        <Button
          variant="outlined"
          onClick={() => rows.length && exportToCSV(rows, 'report.csv')}
          disabled={rows.length === 0}
        >
          Экспорт в CSV
        </Button>
      </Stack>
      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              {rows[0] && Object.keys(rows[0]).map(key => <TableCell key={key}>{key}</TableCell>)}
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row, idx) => (
              <TableRow key={idx}>
                {Object.values(row).map((val, i) => <TableCell key={i}>{val}</TableCell>)}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      {rows.length === 0 && <Typography color="text.secondary">Нет данных для отчёта</Typography>}
    </Stack>
  );
};

export default Reports; 