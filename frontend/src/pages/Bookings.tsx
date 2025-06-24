import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getBookings, createBooking } from '../services/apiClient';
import { Booking } from '../types/booking';
import Stack from '@mui/material/Stack';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import Snackbar from '@mui/material/Snackbar';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs, { Dayjs } from 'dayjs';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';

const Bookings: React.FC = () => {
  const queryClient = useQueryClient();
  const { data: bookings = [], isLoading, error } = useQuery(['bookings'], () => getBookings());
  const [selectedDate, setSelectedDate] = React.useState<Dayjs>(dayjs());
  const [addOpen, setAddOpen] = React.useState(false);
  const [addClientId, setAddClientId] = React.useState('');
  const [addClassType, setAddClassType] = React.useState('');
  const [addLoading, setAddLoading] = React.useState(false);
  const [snackbar, setSnackbar] = React.useState<{ open: boolean; message: string }>({ open: false, message: '' });

  const mutation = useMutation(createBooking, {
    onSuccess: () => {
      setSnackbar({ open: true, message: 'Запись добавлена' });
      setAddOpen(false);
      setAddClientId('');
      setAddClassType('');
      queryClient.invalidateQueries(['bookings']);
      setAddLoading(false);
    },
    onError: () => {
      setSnackbar({ open: true, message: 'Ошибка при добавлении записи' });
      setAddLoading(false);
    },
  });

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setAddLoading(true);
    mutation.mutate({
      client_id: addClientId,
      class_date: selectedDate.toISOString(),
      class_type: addClassType,
    });
  };

  const filtered = bookings.filter(b => dayjs(b.class_date).isSame(selectedDate, 'day'));

  let errorMessage = '';
  if (error) {
    if (error instanceof Error) {
      errorMessage = error.message;
    } else {
      errorMessage = String(error);
    }
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Stack spacing={3} sx={{ p: 3 }}>
        <Typography variant="h5" fontWeight={700} mb={2}>
          Календарь занятий
        </Typography>
        <DatePicker
          label="Выберите дату"
          value={selectedDate}
          onChange={date => date && setSelectedDate(date)}
          sx={{ maxWidth: 240 }}
        />
        <Button variant="contained" onClick={() => setAddOpen(true)} sx={{ maxWidth: 240 }}>
          Добавить запись
        </Button>
        <Typography variant="subtitle1" fontWeight={600} mt={2} mb={1}>
          Занятия на {selectedDate.format('DD.MM.YYYY')}
        </Typography>
        {isLoading && <Typography>Загрузка...</Typography>}
        {errorMessage && (
          <Typography color="error">
            Ошибка загрузки расписания: {errorMessage}
          </Typography>
        )}
        {!isLoading && !errorMessage && filtered.length === 0 && (
          <Typography color="text.secondary">Доступных занятий не найдено</Typography>
        )}
        <Stack spacing={1}>
          {filtered.map(b => (
            <Stack key={b.id} direction="row" spacing={2} alignItems="center" sx={{ bgcolor: '#f5f5f5', borderRadius: 2, p: 2 }}>
              <Typography>{b.class_type}</Typography>
              <Typography color="text.secondary">Клиент: {b.client_id}</Typography>
              <Typography color="text.secondary">Статус: {b.status}</Typography>
            </Stack>
          ))}
        </Stack>
        <Dialog open={addOpen} onClose={() => setAddOpen(false)} maxWidth="xs" fullWidth>
          <DialogTitle>Добавить запись</DialogTitle>
          <form onSubmit={handleAddSubmit}>
            <DialogContent>
              <TextField
                label="ID клиента"
                value={addClientId}
                onChange={e => setAddClientId(e.target.value)}
                fullWidth
                required
                margin="normal"
              />
              <TextField
                label="Тип занятия"
                value={addClassType}
                onChange={e => setAddClassType(e.target.value)}
                fullWidth
                required
                margin="normal"
              />
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setAddOpen(false)}>Отмена</Button>
              <Button type="submit" variant="contained" disabled={addLoading}>
                {addLoading ? 'Добавляем...' : 'Добавить'}
              </Button>
            </DialogActions>
          </form>
        </Dialog>
        <Snackbar
          open={snackbar.open}
          autoHideDuration={3000}
          onClose={() => setSnackbar({ open: false, message: '' })}
          message={snackbar.message}
        />
      </Stack>
    </LocalizationProvider>
  );
};

export default Bookings; 