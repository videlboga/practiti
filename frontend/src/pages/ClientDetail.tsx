import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useClientDetail, useClientSubscriptions, useClientBookings } from '../hooks/useClients';
import ClientDetailCard from '../components/client/ClientDetailCard';
import SubscriptionForm from '../components/subscription/SubscriptionForm';
import Dialog from '@mui/material/Dialog';
import { giftClassToSubscription, deleteSubscription, confirmSubscriptionPayment } from '../services/apiClient';
import Snackbar from '@mui/material/Snackbar';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Button from '@mui/material/Button';
import BookingForm from '../components/booking/BookingForm';

const ClientDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: client, isLoading, error } = useClientDetail(id || '');
  const { data: subscriptions = [], isLoading: loadingSubs, error: errorSubs, refetch: refetchSubs } = useClientSubscriptions(id || '');
  const { data: bookings = [], isLoading: loadingBookings, error: errorBookings, refetch: refetchBookings } = useClientBookings(id || '');
  const [editSub, setEditSub] = React.useState<null | import('../types/subscription').Subscription>(null);
  const [addSubOpen, setAddSubOpen] = React.useState(false);
  const [snackbar, setSnackbar] = React.useState<{ open: boolean; message: string }>({ open: false, message: '' });
  const [deleteSubId, setDeleteSubId] = React.useState<string | null>(null);
  const [addBookingOpen, setAddBookingOpen] = React.useState(false);

  const handleGiftClass = async (subId: string) => {
    try {
      await giftClassToSubscription(subId);
      setSnackbar({ open: true, message: 'Занятие успешно подарено!' });
      refetchSubs();
      refetchBookings();
    } catch {
      setSnackbar({ open: true, message: 'Ошибка при подарке занятия' });
    }
  };

  const handleDeleteSubscription = async () => {
    if (!deleteSubId) return;
    try {
      await deleteSubscription(deleteSubId);
      setSnackbar({ open: true, message: 'Абонемент удалён' });
      setDeleteSubId(null);
      refetchSubs();
      refetchBookings();
    } catch {
      setSnackbar({ open: true, message: 'Ошибка при удалении абонемента' });
    }
  };

  const handleConfirmPayment = async (subId: string) => {
    try {
      await confirmSubscriptionPayment(subId);
      setSnackbar({ open: true, message: 'Оплата подтверждена' });
      refetchSubs();
    } catch {
      setSnackbar({ open: true, message: 'Ошибка подтверждения оплаты' });
    }
  };

  if (isLoading) return <div>Загрузка...</div>;
  if (error) return <div>Ошибка загрузки: {error.message}</div>;
  if (!client) return <div>Клиент не найден</div>;

  return (
    <>
      <ClientDetailCard
        client={client}
        onEdit={() => navigate(`/clients/${client.id}/edit`)}
        onAddSubscription={() => setAddSubOpen(true)}
        subscriptions={subscriptions}
        onDelete={() => {/* TODO: реализовать удаление */}}
        loadingSubscriptions={loadingSubs}
        errorSubscriptions={errorSubs ? errorSubs.message : null}
        bookings={bookings}
        loadingBookings={loadingBookings}
        errorBookings={errorBookings ? errorBookings.message : null}
        onEditSubscription={setEditSub}
        onGiftClassSubscription={handleGiftClass}
        onConfirmPayment={handleConfirmPayment}
        onDeleteSubscription={setDeleteSubId}
        onAddBooking={() => setAddBookingOpen(true)}
      />
      <Dialog open={!!editSub} onClose={() => setEditSub(null)} maxWidth="xs" fullWidth>
        {editSub && (
          <SubscriptionForm
            clientId={client.id}
            editMode
            subscription={editSub}
            onSuccess={() => {
              setEditSub(null);
              refetchSubs();
              refetchBookings();
            }}
            onCancel={() => setEditSub(null)}
          />
        )}
      </Dialog>
      <Dialog open={!!deleteSubId} onClose={() => setDeleteSubId(null)}>
        <DialogTitle>Удалить абонемент?</DialogTitle>
        <DialogContent>Вы уверены, что хотите удалить этот абонемент? Это действие необратимо.</DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteSubId(null)}>Отмена</Button>
          <Button onClick={handleDeleteSubscription} color="error" variant="contained">Удалить</Button>
        </DialogActions>
      </Dialog>
      <Dialog open={addSubOpen} onClose={() => setAddSubOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Новый абонемент</DialogTitle>
        <DialogContent>
          <SubscriptionForm
            clientId={client.id}
            onSuccess={() => {
              setAddSubOpen(false);
              refetchSubs();
              refetchBookings();
            }}
            onCancel={() => setAddSubOpen(false)}
          />
        </DialogContent>
      </Dialog>
      <BookingForm
        open={addBookingOpen}
        onClose={() => setAddBookingOpen(false)}
        clientId={client.id}
        subscriptions={subscriptions}
        onCreated={() => {
          refetchBookings();
        }}
      />
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ open: false, message: '' })}
        message={snackbar.message}
      />
    </>
  );
};

export default ClientDetail; 