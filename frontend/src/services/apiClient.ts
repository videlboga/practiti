import axios from 'axios';
import { Client, ClientCreateData } from '../types/client';
import { Subscription, SubscriptionCreateData, SubscriptionUpdateData } from '../types/subscription';
import { Booking, BookingCreateData } from '../types/booking';

// Если переменная окружения не задана, используем порт 8888
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8888';

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// ---------------------------------------------------------------------------
// Интерцептор ошибок – преобразует HTTP-ошибку бэкенда в Error с понятным
// сообщением (detail). Все сервисы и React-Query мутации смогут показывать
// err.message напрямую.
// ---------------------------------------------------------------------------

api.interceptors.response.use(
  (response) => response,
  (error) => {
    let message = 'Неизвестная ошибка';

    if (error.response) {
      // Ответ получен, но код не 2xx – берём detail из FastAPI
      const data = error.response.data || {};
      if (typeof data === 'string') {
        message = data;
      } else {
        message = data.detail || data.message || error.response.statusText;
      }
    } else if (error.request) {
      // Запрос ушёл, но ответа нет – возможно, сеть или CORS
      message = 'Сервер не отвечает. Проверьте соединение или попробуйте позднее.';
    } else if (error.message) {
      message = error.message;
    }

    return Promise.reject(new Error(message));
  },
);

export interface GetClientsParams {
  page?: number;
  pageSize?: number;
  search?: string;
  status?: string;
}

// Клиенты
export const getClients = async (params: GetClientsParams = {}): Promise<{ data: Client[]; total: number }> => {
  const { data } = await api.get('/api/clients/', { params });
  // Бэкенд возвращает { items, total, ... }
  return {
    // @ts-ignore – runtime ok, типы совпадут после маппинга
    data: data.items ?? data.data ?? [],
    total: data.total ?? 0,
  };
};

export const getClientById = async (id: string): Promise<Client> => {
  const { data } = await api.get<Client>(`/api/clients/${id}`);
  return data;
};

export const createClient = async (client: ClientCreateData): Promise<Client> => {
  const { data } = await api.post<Client>('/api/clients/', client);
  return data;
};

// Абонементы
export const getSubscriptions = async (): Promise<Subscription[]> => {
  const { data } = await api.get<Subscription[]>('/api/subscriptions/');
  return data;
};

export const getSubscriptionsByClientId = async (clientId: string): Promise<Subscription[]> => {
  const { data } = await api.get<Subscription[]>(`/api/clients/${clientId}/subscriptions`);
  return data;
};

export const createSubscription = async (sub: SubscriptionCreateData): Promise<Subscription> => {
  // Бэкенд ожидает subscription_type, поэтому маппим поле
  const payload = {
    client_id: sub.client_id,
    subscription_type: sub.type,
    // Дополнительные поля пока не требуются (MVP)
  } as any;
  const { data } = await api.post<Subscription>('/api/subscriptions/', payload);
  return data;
};

export const updateSubscription = async (id: string, data: SubscriptionUpdateData): Promise<Subscription> => {
  const res = await api.put<Subscription>(`/api/subscriptions/${id}`, data);
  return res.data;
};

export const giftClassToSubscription = async (id: string): Promise<Subscription> => {
  const res = await api.post<Subscription>(`/api/subscriptions/${id}/gift-class`);
  return res.data;
};

export const deleteSubscription = async (id: string): Promise<void> => {
  await api.delete(`/api/subscriptions/${id}`);
};

export const freezeSubscription = async (id: string, days: number, reason?: string): Promise<Subscription> => {
  const res = await api.patch<Subscription>(
    `/api/subscriptions/${id}/freeze`,
    null,
    { params: { days, ...(reason ? { reason } : {}) } },
  );
  return res.data;
};

export const confirmSubscriptionPayment = async (id: string): Promise<Subscription> => {
  const res = await api.patch<Subscription>(`/api/subscriptions/${id}/confirm-payment`);
  return res.data;
};

// Занятия
export interface GetBookingsParams {
  client_id?: string;
  date?: string; // ISO date
}

export const getBookings = async (params: GetBookingsParams = {}): Promise<Booking[]> => {
  const { data } = await api.get<Booking[]>('/api/bookings/', { params });
  return data;
};

export const getBookingsByClientId = async (clientId: string): Promise<Booking[]> => {
  return getBookings({ client_id: clientId });
};

export const createBooking = async (booking: BookingCreateData): Promise<Booking> => {
  const { data } = await api.post<Booking>('/api/bookings/', booking);
  return data;
};

export interface DashboardMetrics {
  totalClients: number;
  activeClients: number;
  totalSubscriptions: number;
  activeSubscriptions: number;
  totalBookings: number;
  bookingsThisMonth: number;
}

export const getDashboardMetrics = async (): Promise<DashboardMetrics> => {
  const { data } = await api.get<DashboardMetrics>('/api/analytics/dashboard/metrics');
  return data;
}; 