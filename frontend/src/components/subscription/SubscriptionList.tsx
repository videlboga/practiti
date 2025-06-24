import React from 'react';
import { Subscription } from '../../types/subscription';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Stack from '@mui/material/Stack';
import Button from '@mui/material/Button';

interface SubscriptionListProps {
  subscriptions: Subscription[];
  onEdit?: (id: string) => void;
  onExtend?: (id: string) => void;
  onDelete?: (id: string) => void;
  onGiftClass?: (id: string) => void;
  onConfirmPayment?: (id: string) => void;
  onFreeze?: (id: string) => void;
}

const typeLabels: Record<string, string> = {
  trial: 'Пробное',
  single: 'Разовое',
  newbie4: 'Новичок (4)',
  regular4: '4 занятия',
  regular8: '8 занятий',
  regular12: '12 занятий',
  unlimited: 'Безлимит',
};

const statusColors: Record<string, string> = {
  active: '#7cb342',
  inactive: '#bdbdbd',
  expired: '#e57373',
};

/**
 * Список абонементов клиента с action-кнопками
 */
const SubscriptionList: React.FC<SubscriptionListProps> = ({ subscriptions, onEdit, onExtend, onDelete, onGiftClass, onConfirmPayment, onFreeze }) => {
  if (!subscriptions.length) {
    return <Typography color="text.secondary">Нет абонементов</Typography>;
  }
  return (
    <Stack spacing={2}>
      {subscriptions.map((sub) => (
        <Card key={sub.id} variant="outlined" sx={{ borderRadius: 2, boxShadow: 1 }}>
          <CardContent>
            <Typography variant="subtitle1" fontWeight={600} mb={1}>
              {typeLabels[sub.type] || sub.type}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {sub.start_date} — {sub.end_date}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Осталось занятий: {sub.remaining_classes} из {sub.total_classes}
            </Typography>
            <Typography variant="body2" sx={{ color: statusColors[sub.status], fontWeight: 600 }}>
              {sub.status === 'active' ? 'Активен' : sub.status === 'expired' ? 'Истёк' : 'Неактивен'}
            </Typography>
            <Stack direction="row" spacing={1} mt={2}>
              {sub.status === 'pending' && onConfirmPayment && (
                <Button variant="contained" color="success" size="small" fullWidth onClick={() => onConfirmPayment(sub.id)}>
                  Подтвердить оплату
                </Button>
              )}
              {onEdit && (
                <Button variant="outlined" size="small" fullWidth onClick={() => onEdit(sub.id)}>
                  Редактировать
                </Button>
              )}
              {onExtend && (
                <Button variant="outlined" size="small" fullWidth onClick={() => onExtend(sub.id)}>
                  Продлить
                </Button>
              )}
              {onFreeze && (
                <Button variant="outlined" size="small" fullWidth onClick={() => onFreeze(sub.id)}>
                  Заморозить
                </Button>
              )}
              {onDelete && (
                <Button variant="outlined" color="error" size="small" fullWidth onClick={() => onDelete(sub.id)}>
                  Удалить
                </Button>
              )}
              {onGiftClass && (
                <Button variant="outlined" size="small" fullWidth onClick={() => onGiftClass(sub.id)}>
                  Подарить занятие
                </Button>
              )}
            </Stack>
          </CardContent>
        </Card>
      ))}
    </Stack>
  );
};

export default SubscriptionList;
