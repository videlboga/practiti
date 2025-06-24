import React from 'react';
import { useClients, ClientFilters } from '../hooks/useClients';
import ClientList from '../components/client/ClientList';
import ClientSearchBar from '../components/client/ClientSearchBar';
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import AddIcon from '@mui/icons-material/Add';
import CardGiftcardIcon from '@mui/icons-material/CardGiftcard';
import { useNavigate } from 'react-router-dom';
import { Client } from '../types/client';
import Pagination from '@mui/material/Pagination';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import TextField from '@mui/material/TextField';
import Snackbar from '@mui/material/Snackbar';
import { createClient } from '../services/apiClient';

const Clients: React.FC = () => {
  const [search, setSearch] = React.useState('');
  const [status, setStatus] = React.useState<string>('');
  const [page, setPage] = React.useState(1);
  const pageSize = 10;
  const filters: ClientFilters = { search, status };
  const { data, isLoading, error } = useClients(page, pageSize, filters);
  const clients = data?.data || [];
  const total = data?.total || 0;
  const pageCount = Math.ceil(total / pageSize);
  const navigate = useNavigate();
  const [addOpen, setAddOpen] = React.useState(false);
  const [addName, setAddName] = React.useState('');
  const [addPhone, setAddPhone] = React.useState('');
  const [addLoading, setAddLoading] = React.useState(false);
  const [snackbar, setSnackbar] = React.useState<{ open: boolean; message: string }>({ open: false, message: '' });
  const { refetch } = useClients(page, pageSize, filters);
  const [nameError, setNameError] = React.useState('');
  const [phoneError, setPhoneError] = React.useState('');

  const handleAddClient = (client: Client) => {
    // Implementation of handleAddClient
  };

  const handleQuickAdd = () => setAddOpen(true);
  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAddLoading(true);
    try {
      let valid = true;
      if (addName.trim().length < 2) {
        setNameError('Минимум 2 символа');
        valid = false;
      } else {
        setNameError('');
      }

      const phoneRegex = /^\+7\d{10}$/;
      if (!phoneRegex.test(addPhone.trim())) {
        setPhoneError('Формат +7XXXXXXXXXX');
        valid = false;
      } else {
        setPhoneError('');
      }

      if (!valid) {
        return;
      }

      await createClient({ name: addName, phone: addPhone });
      setSnackbar({ open: true, message: 'Клиент добавлен' });
      setAddOpen(false);
      setAddName('');
      setAddPhone('');
      refetch();
    } catch (err: any) {
      setSnackbar({ open: true, message: err?.message || 'Ошибка при добавлении клиента' });
    } finally {
      setAddLoading(false);
    }
  };

  return (
    <Stack spacing={3}>
      <Typography variant="h5" fontWeight={700} mt={1} mb={1}>
        Клиенты
      </Typography>
      <ClientSearchBar value={search} onChange={setSearch} />
      <Stack direction="row" spacing={2} alignItems="center" mb={1}>
        <Select
          value={status}
          onChange={e => setStatus(e.target.value)}
          displayEmpty
          sx={{ minWidth: 160 }}
        >
          <MenuItem value="">Все статусы</MenuItem>
          <MenuItem value="active">Активные</MenuItem>
          <MenuItem value="inactive">Неактивные</MenuItem>
        </Select>
      </Stack>
      <Stack direction="column" spacing={2} mb={1}>
        <Button variant="outlined" startIcon={<AddIcon />} sx={{ borderRadius: 2 }} fullWidth onClick={handleQuickAdd}>
          Добавить нового клиента
        </Button>
      </Stack>
      {isLoading && <Typography>Загрузка...</Typography>}
      {error && <Typography color="error">Ошибка загрузки</Typography>}
      <Typography variant="subtitle1" fontWeight={600} mt={2} mb={1}>
        Результаты поиска
      </Typography>
      <ClientList
        clients={clients}
        onAdd={handleAddClient}
        onCardClick={(id) => navigate(`/clients/${id}`)}
      />
      {pageCount > 1 && (
        <Pagination
          count={pageCount}
          page={page}
          onChange={(_, value) => setPage(value)}
          sx={{ mt: 2, alignSelf: 'center' }}
        />
      )}
      <Dialog open={addOpen} onClose={() => setAddOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Быстрое добавление клиента</DialogTitle>
        <form onSubmit={handleAddSubmit}>
          <DialogContent>
            <TextField
              label="Имя"
              value={addName}
              onChange={e => setAddName(e.target.value)}
              error={Boolean(nameError)}
              helperText={nameError || ' '}
              fullWidth
              required
              margin="normal"
            />
            <TextField
              label="Телефон"
              value={addPhone}
              onChange={e => setAddPhone(e.target.value)}
              error={Boolean(phoneError)}
              helperText={phoneError || ' '}
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
  );
};

export default Clients; 