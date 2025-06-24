import { render, screen, fireEvent } from '@testing-library/react';
import ClientDetailCard from './ClientDetailCard';
import { Client } from '../../types/client';

describe('ClientDetailCard', () => {
  const mockClient: Client = {
    id: '1',
    name: 'Иван Иванов',
    phone: '+79991234567',
    telegram_id: 123456789,
    yoga_experience: true,
    intensity_preference: 'Поспокойней',
    time_preference: 'Будни утро',
    created_at: '2023-01-01T10:00:00Z',
    status: 'active',
  };

  it('отображает всю информацию о клиенте', () => {
    render(<ClientDetailCard client={mockClient} />);
    expect(screen.getByText('Иван Иванов')).toBeInTheDocument();
    expect(screen.getByText('+79991234567')).toBeInTheDocument();
    expect(screen.getByText('123456789')).toBeInTheDocument();
    expect(screen.getByText('Да')).toBeInTheDocument();
    expect(screen.getByText('Поспокойней')).toBeInTheDocument();
    expect(screen.getByText('Будни утро')).toBeInTheDocument();
    expect(screen.getByText('Активен')).toBeInTheDocument();
  });

  it('вызывает onEdit при клике по кнопке', () => {
    const onEdit = jest.fn();
    render(<ClientDetailCard client={mockClient} onEdit={onEdit} />);
    fireEvent.click(screen.getByText('Редактировать'));
    expect(onEdit).toHaveBeenCalledWith('1');
  });

  it('вызывает onAddSubscription при клике по кнопке', () => {
    const onAddSubscription = jest.fn();
    render(<ClientDetailCard client={mockClient} onAddSubscription={onAddSubscription} />);
    fireEvent.click(screen.getByText('Добавить абонемент'));
    expect(onAddSubscription).toHaveBeenCalledWith('1');
  });

  it('вызывает onGiftClass при клике по кнопке', () => {
    const onGiftClass = jest.fn();
    render(<ClientDetailCard client={mockClient} onGiftClass={onGiftClass} />);
    fireEvent.click(screen.getByText('Подарить занятие'));
    expect(onGiftClass).toHaveBeenCalledWith('1');
  });

  it('вызывает onDelete при клике по кнопке', () => {
    const onDelete = jest.fn();
    render(<ClientDetailCard client={mockClient} onDelete={onDelete} />);
    fireEvent.click(screen.getByText('Удалить'));
    expect(onDelete).toHaveBeenCalledWith('1');
  });
}); 