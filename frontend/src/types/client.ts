export interface Client {
  id: string;
  name: string;
  phone: string;
  telegram_id: number;
  yoga_experience: boolean;
  intensity_preference: string;
  time_preference: string;
  created_at: string; // ISO date
  status: 'active' | 'inactive';
}

export interface ClientCreateData {
  name: string;
  phone: string;
  telegram_id?: number;
  yoga_experience?: boolean;
  intensity_preference?: string;
  time_preference?: string;
} 