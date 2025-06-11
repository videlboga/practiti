# 🤖 CURSOR RULES - ЧАСТЬ 3: ТЕСТИРОВАНИЕ И ПРОВЕРКИ

## 🧪 ТЕСТИРОВАНИЕ

### Component Test Pattern:
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@mui/material/styles';
import { ClientCard } from './ClientCard';
import { mockClient } from '../../test-utils/mocks';
import { theme } from '../../theme';

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        {children}
      </ThemeProvider>
    </QueryClientProvider>
  );
};

describe('ClientCard', () => {
  it('отображает информацию о клиенте', () => {
    render(<ClientCard client={mockClient} />, { wrapper: createWrapper() });
    
    expect(screen.getByText(mockClient.name)).toBeInTheDocument();
    expect(screen.getByText(mockClient.phone)).toBeInTheDocument();
  });

  it('вызывает onEdit при клике на кнопку редактирования', () => {
    const mockOnEdit = jest.fn();
    render(<ClientCard client={mockClient} onEdit={mockOnEdit} />, 
           { wrapper: createWrapper() });
    
    fireEvent.click(screen.getByTestId('edit-button'));
    
    expect(mockOnEdit).toHaveBeenCalledWith(mockClient.id);
  });
});
```

### Hook Test Pattern:
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useClients } from './useClients';
import { clientApi } from '../services/clientApi';

jest.mock('../services/clientApi');
const mockedClientApi = clientApi as jest.Mocked<typeof clientApi>;

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('useClients', () => {
  it('загружает список клиентов', async () => {
    const mockClients = [{ id: '1', name: 'Test Client' }];
    mockedClientApi.getClients.mockResolvedValue(mockClients);

    const { result } = renderHook(() => useClients(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.clients).toEqual(mockClients);
    });
  });
});
```

---

## ✅ ЧЕКЛИСТ ЗАВЕРШЕНИЯ СЕССИИ

### Обязательно проверить:
- [ ] Все компоненты типизированы (TypeScript)
- [ ] Нет any типов
- [ ] Responsive дизайн работает
- [ ] Accessibility атрибуты добавлены
- [ ] Loading/error состояния обработаны
- [ ] Тесты написаны и проходят
- [ ] ESLint проверки пройдены
- [ ] Нет console.log/console.error

### Финальные команды:
```bash
# Проверки
npm run type-check
npm run lint
npm test --coverage
npm run build

# Только после успешных проверок - коммит!
git add .
git commit -m "feat(frontend): описание фичи"
```

---

## 🚫 КРАСНЫЕ ФЛАГИ

**СТОП! НЕ КОММИТЬ, если:**
- ❌ TypeScript ошибки
- ❌ ESLint warnings
- ❌ Тесты падают
- ❌ Build fails
- ❌ Компонент >300 строк
- ❌ Any типы
- ❌ Inline стили
- ❌ console.log отладка

---

**ПОМНИ: Простота превыше всего! Каждый компонент должен делать одну вещь хорошо.** 