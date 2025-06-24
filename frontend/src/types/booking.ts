export type BookingStatus = 'active' | 'cancelled' | 'completed';

export interface Booking {
  id: string;
  client_id: string;
  class_date: string; // ISO date
  class_type: string;
  status: BookingStatus;
  created_at: string; // ISO date
}

export interface BookingCreateData {
  client_id: string;
  class_date: string;
  class_type: string;
  subscription_id?: string;
} 