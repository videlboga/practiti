import React from 'react';
import { Client } from '../../types/client';
import Button from '../common/Button';
import SubscriptionList from '../subscription/SubscriptionList';
import BookingList from '../booking/BookingList';

/**
 * Пропсы для детальной карточки клиента
 */
interface ClientDetailCardProps {
  client: Client;
  onEdit?: (id: string) => void;
  onAddSubscription?: (id: string) => void;
  onGiftClass?: (id: string) => void;
  onDelete?: (id: string) => void;
  subscriptions?: import('../../types/subscription').Subscription[];
  loadingSubscriptions?: boolean;
  errorSubscriptions?: string | null;
  onEditSubscription?: (sub: import('../../types/subscription').Subscription) => void;
  onGiftClassSubscription?: (id: string) => void;
  onDeleteSubscription?: (id: string) => void;
  bookings?: import('../../types/booking').Booking[];
  loadingBookings?: boolean;
  errorBookings?: string | null;
  onConfirmPayment?: (id: string) => void;
}

const labelStyle: React.CSSProperties = {
  color: '#8d7964',
  fontWeight: 500,
  fontSize: 14,
  marginBottom: 2,
};

const valueStyle: React.CSSProperties = {
  color: '#3e2723',
  fontWeight: 600,
  fontSize: 16,
  marginBottom: 8,
};

const cardStyle: React.CSSProperties = {
  background: '#fff',
  borderRadius: 16,
  boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
  padding: 24,
  maxWidth: 400,
  margin: '0 auto',
  display: 'flex',
  flexDirection: 'column',
  gap: 8,
};

const buttonRowStyle: React.CSSProperties = {
  display: 'flex',
  gap: 12,
  marginTop: 16,
  flexWrap: 'wrap',
};

const statusColors: Record<string, string> = {
  active: '#7cb342',
  inactive: '#bdbdbd',
};

/**
 * Детальная карточка клиента с действиями
 */
const ClientDetailCard: React.FC<ClientDetailCardProps> = ({
  client,
  onEdit,
  onAddSubscription,
  onGiftClass,
  onDelete,
  subscriptions = [],
  loadingSubscriptions = false,
  errorSubscriptions = null,
  onEditSubscription,
  onGiftClassSubscription,
  onDeleteSubscription,
  bookings = [],
  loadingBookings = false,
  errorBookings = null,
  onConfirmPayment,
}) => {
  return (
    <div style={cardStyle} data-testid="client-detail-card">
      <h2 style={{ color: '#3e2723', marginBottom: 12 }}>{client.name}</h2>
      <div>
        <div style={labelStyle}>Телефон:</div>
        <div style={valueStyle}>{client.phone}</div>
      </div>
      <div>
        <div style={labelStyle}>Telegram ID:</div>
        <div style={valueStyle}>{client.telegram_id || '—'}</div>
      </div>
      <div>
        <div style={labelStyle}>Опыт йоги:</div>
        <div style={valueStyle}>{client.yoga_experience ? 'Да' : 'Нет'}</div>
      </div>
      <div>
        <div style={labelStyle}>Предпочтения по интенсивности:</div>
        <div style={valueStyle}>{client.intensity_preference || '—'}</div>
      </div>
      <div>
        <div style={labelStyle}>Удобное время:</div>
        <div style={valueStyle}>{client.time_preference || '—'}</div>
      </div>
      <div>
        <div style={labelStyle}>Дата создания:</div>
        <div style={valueStyle}>{new Date(client.created_at).toLocaleDateString()}</div>
      </div>
      <div>
        <div style={labelStyle}>Статус:</div>
        <div style={{ ...valueStyle, color: statusColors[client.status] || '#bdbdbd' }}>{client.status === 'active' ? 'Активен' : 'Неактивен'}</div>
      </div>
      <div style={buttonRowStyle}>
        <Button onClick={() => onEdit?.(client.id)}>Редактировать</Button>
        <Button onClick={() => onAddSubscription?.(client.id)}>Добавить абонемент</Button>
        <Button onClick={() => onGiftClass?.(client.id)}>Подарить занятие</Button>
        <Button onClick={() => onDelete?.(client.id)} style={{ background: '#e57373' }}>Удалить</Button>
      </div>
      <div style={{ marginTop: 24 }}>
        <div style={{ ...labelStyle, marginBottom: 8 }}>История абонементов:</div>
        {loadingSubscriptions && <div>Загрузка абонементов...</div>}
        {errorSubscriptions && <div style={{ color: 'red' }}>{errorSubscriptions}</div>}
        {!loadingSubscriptions && !errorSubscriptions && (
          <SubscriptionList
            subscriptions={subscriptions}
            onConfirmPayment={onConfirmPayment}
            onEdit={sub => onEditSubscription?.(subscriptions.find(s => s.id === sub)!)}
            onGiftClass={onGiftClassSubscription}
            onDelete={onDeleteSubscription}
          />
        )}
      </div>
      <div style={{ marginTop: 24 }}>
        <div style={{ ...labelStyle, marginBottom: 8 }}>Записи на занятия:</div>
        {loadingBookings && <div>Загрузка записей...</div>}
        {errorBookings && <div style={{ color: 'red' }}>{errorBookings}</div>}
        {!loadingBookings && !errorBookings && (
          <BookingList bookings={bookings} />
        )}
      </div>
    </div>
  );
};

export default ClientDetailCard; 