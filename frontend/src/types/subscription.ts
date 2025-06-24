export type SubscriptionType =
  | 'trial'
  | 'single'
  | 'package_4'
  | 'package_8'
  | 'package_12'
  | 'unlimited';

export type SubscriptionStatus = 'pending' | 'active' | 'expired' | 'exhausted' | 'inactive' | 'suspended';

export interface Subscription {
  id: string;
  client_id: string;
  type: SubscriptionType;
  total_classes: number;
  used_classes: number;
  remaining_classes: number;
  start_date: string; // ISO date
  end_date: string; // ISO date
  status: SubscriptionStatus;
  payment_confirmed?: boolean;
}

export interface SubscriptionCreateData {
  client_id: string;
  type: SubscriptionType;
}

export interface SubscriptionUpdateData {
  type?: SubscriptionType;
  status?: SubscriptionStatus;
  end_date?: string;
} 