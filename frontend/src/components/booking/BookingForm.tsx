import React from 'react';
import { CLASS_SLOTS } from '../../constants/classSlots';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import { Subscription } from '../../types/subscription';
import { createBooking } from '../../services/apiClient';
import { BookingCreateData } from '../../types/booking';

interface BookingFormProps {
  open: boolean;
  onClose: () => void;
  clientId: string;
  subscriptions: Subscription[];
  onCreated: () => void;
}

const BookingForm: React.FC<BookingFormProps> = ({ open, onClose, clientId, subscriptions, onCreated }) => {
  const [slotValue, setSlotValue] = React.useState(CLASS_SLOTS[0].value);
  const [subscriptionId, setSubscriptionId] = React.useState<string | ''>('');
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    // preselect first active subscription if exists
    const active = subscriptions.find((s) => s.status === 'active');
    if (active) setSubscriptionId(active.id);
  }, [subscriptions]);

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const slotMeta = CLASS_SLOTS.find((s) => s.value === slotValue)!;
      const payload: BookingCreateData & { subscription_id?: string } = {
        client_id: clientId,
        class_date: slotValue,
        class_type: slotMeta.classType,
      } as any;
      if (subscriptionId) {
        (payload as any).subscription_id = subscriptionId;
      }
      await createBooking(payload as any);
      onCreated();
      onClose();
    } catch (e: any) {
      // eslint-disable-next-line no-alert
      alert(e?.message || 'Ошибка при создании бронирования');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>Записать на занятие</DialogTitle>
      <DialogContent sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
        <TextField
          select
          label="Выберите занятие"
          value={slotValue}
          onChange={(e) => setSlotValue(e.target.value)}
        >
          {CLASS_SLOTS.map((slot) => (
            <MenuItem key={slot.value} value={slot.value}>
              {slot.label}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          label="Абонемент"
          value={subscriptionId}
          onChange={(e) => setSubscriptionId(e.target.value)}
          helperText="Если оставить пустым — будет выбран активный по умолчанию"
        >
          <MenuItem value="">Авто</MenuItem>
          {subscriptions.map((s) => (
            <MenuItem key={s.id} value={s.id}>
              {s.type} / осталось {s.remaining_classes}
            </MenuItem>
          ))}
        </TextField>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Отмена</Button>
        <Button onClick={handleSubmit} disabled={loading} variant="contained">
          Создать
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default BookingForm; 