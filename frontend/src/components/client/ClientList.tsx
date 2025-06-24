import React from 'react';
import { Client } from '../../types/client';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Stack from '@mui/material/Stack';

/**
 * Пропсы для списка клиентов
 */
interface ClientListProps {
  clients: Client[];
  onAdd: (client: Client) => void;
  onCardClick?: (id: string) => void;
  onQuickAdd?: () => void;
}

/**
 * Список клиентов с возможностью перехода к деталям и добавления
 */
const ClientList: React.FC<ClientListProps> = ({ clients, onAdd, onCardClick }) => {
  if (clients.length === 0) {
    return <Typography color="text.secondary">Нет клиентов</Typography>;
  }
  return (
    <Stack spacing={2}>
      {clients.map((client) => (
        <Card
          key={client.id}
          variant="outlined"
          sx={{ borderRadius: 2, boxShadow: 1, bgcolor: 'background.paper', cursor: onCardClick ? 'pointer' : 'default' }}
          onClick={() => onCardClick?.(client.id)}
        >
          <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', p: 2 }}>
            <div>
              <Typography variant="subtitle1" fontWeight={600}>{client.name}</Typography>
              <Typography variant="body2" color="text.secondary">{client.phone}</Typography>
            </div>
            <Button onClick={e => { e.stopPropagation(); onAdd(client); }}>Добавить</Button>
          </CardContent>
        </Card>
      ))}
    </Stack>
  );
};

export default ClientList; 