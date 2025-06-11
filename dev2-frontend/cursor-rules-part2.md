# 🤖 CURSOR RULES - ЧАСТЬ 2: ШАБЛОНЫ

## 📝 ОБЯЗАТЕЛЬНЫЕ ШАБЛОНЫ КОМПОНЕНТОВ

### React Component Pattern:
```typescript
import React from 'react';
import { styled } from '@mui/material/styles';
import { Box, Typography } from '@mui/material';
import { Client } from '../../types/client';

interface ClientCardProps {
  client: Client;
  onEdit?: (clientId: string) => void;
  onDelete?: (clientId: string) => void;
  loading?: boolean;
}

const StyledCard = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  border: `1px solid ${theme.palette.divider}`,
  borderRadius: theme.shape.borderRadius,
  '&:hover': {
    backgroundColor: theme.palette.action.hover,
  },
}));

export const ClientCard: React.FC<ClientCardProps> = ({
  client,
  onEdit,
  onDelete,
  loading = false,
}) => {
  const handleEdit = () => {
    onEdit?.(client.id);
  };

  const handleDelete = () => {
    if (window.confirm('Удалить клиента?')) {
      onDelete?.(client.id);
    }
  };

  if (loading) {
    return <div>Загрузка...</div>;
  }

  return (
    <StyledCard data-testid="client-card">
      <Typography variant="h6">{client.name}</Typography>
      <Typography variant="body2">{client.phone}</Typography>
      {/* Остальной JSX */}
    </StyledCard>
  );
};
```

### Custom Hook Pattern:
```typescript
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { clientApi } from '../services/clientApi';
import { Client, ClientCreateData } from '../types/client';

export const useClients = () => {
  const queryClient = useQueryClient();

  const {
    data: clients,
    isLoading,
    error
  } = useQuery({
    queryKey: ['clients'],
    queryFn: clientApi.getClients,
  });

  const createMutation = useMutation({
    mutationFn: clientApi.createClient,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
    },
  });

  return {
    clients: clients || [],
    isLoading,
    error,
    createClient: createMutation.mutate,
    isCreating: createMutation.isPending,
  };
};
```

### API Service Pattern:
```typescript
import axios from 'axios';
import { Client, ClientCreateData, ClientUpdateData } from '../types/client';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const clientApi = {
  async getClients(): Promise<Client[]> {
    const response = await apiClient.get<Client[]>('/api/clients');
    return response.data;
  },

  async getClient(id: string): Promise<Client> {
    const response = await apiClient.get<Client>(`/api/clients/${id}`);
    return response.data;
  },

  async createClient(data: ClientCreateData): Promise<Client> {
    const response = await apiClient.post<Client>('/api/clients', data);
    return response.data;
  },

  async updateClient(id: string, data: ClientUpdateData): Promise<Client> {
    const response = await apiClient.put<Client>(`/api/clients/${id}`, data);
    return response.data;
  },
};
``` 