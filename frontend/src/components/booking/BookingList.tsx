import React from 'react';
import { Booking } from '../../types/booking';

interface BookingListProps {
  bookings: Booking[];
}

const listStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: 8,
};

const itemStyle: React.CSSProperties = {
  padding: '8px 12px',
  border: '1px solid #e0e0e0',
  borderRadius: 8,
  background: '#fafafa',
};

const BookingList: React.FC<BookingListProps> = ({ bookings }) => {
  if (bookings.length === 0) return <div>Записей нет</div>;
  return (
    <div style={listStyle} data-testid="booking-list">
      {bookings.map(b => (
        <div key={b.id} style={itemStyle}>
          <div><strong>{new Date(b.class_date).toLocaleString()}</strong> — {b.class_type}</div>
          <div style={{ fontSize: 12, color: '#757575' }}>Статус: {b.status}</div>
        </div>
      ))}
    </div>
  );
};

export default BookingList; 