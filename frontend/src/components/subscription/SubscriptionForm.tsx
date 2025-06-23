import React from 'react';
import { SubscriptionType, SubscriptionStatus, SubscriptionCreateData, SubscriptionUpdateData, Subscription } from '../../types/subscription';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';
import { createSubscription, updateSubscription } from '../../services/apiClient';

interface SubscriptionFormProps {
  clientId: string;
  onSuccess?: () => void;
  onCancel?: () => void;
  editMode?: boolean;
  subscription?: Subscription;
}

const typeOptions: { value: SubscriptionType; label: string }[] = [
  { value: 'trial', label: 'Пробное (1)' },
  { value: 'single', label: 'Разовое (1)' },
  { value: 'package_4', label: 'Пакет 4 занятия' },
  { value: 'package_8', label: 'Пакет 8 занятий' },
  { value: 'package_12', label: 'Пакет 12 занятий' },
  { value: 'unlimited', label: 'Безлимит' },
];

const SubscriptionForm: React.FC<SubscriptionFormProps> = ({ clientId, onSuccess, onCancel, editMode = false, subscription }) => {
  const [type, setType] = React.useState<SubscriptionType>(subscription?.type || 'trial');
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    if (subscription) setType(subscription.type);
  }, [subscription]);

  const validate = () => {
    if (!type) return 'Выберите тип абонемента';
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }
    setLoading(true);
    try {
      if (editMode && subscription) {
        const data: SubscriptionUpdateData = { type };
        await updateSubscription(subscription.id, data);
      } else {
        const data: SubscriptionCreateData = {
          client_id: clientId,
          type,
        };
        await createSubscription(data);
      }
      setLoading(false);
      onSuccess?.();
    } catch (err: any) {
      setError('Ошибка при сохранении абонемента');
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <Stack spacing={2}>
        <TextField
          select
          label="Тип абонемента"
          value={type}
          onChange={e => setType(e.target.value as SubscriptionType)}
          fullWidth
        >
          {typeOptions.map(opt => (
            <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
          ))}
        </TextField>
        {error && <div style={{ color: 'red' }}>{error}</div>}
        <Stack direction="row" spacing={2}>
          <Button type="submit" variant="contained" color="primary" disabled={loading}>
            {loading ? (editMode ? 'Сохраняем...' : 'Сохраняем...') : (editMode ? 'Сохранить изменения' : 'Сохранить')}
          </Button>
          {onCancel && <Button onClick={onCancel} variant="outlined">Отмена</Button>}
        </Stack>
      </Stack>
    </form>
  );
};

export default SubscriptionForm;