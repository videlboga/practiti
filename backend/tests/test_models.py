import pytest
from datetime import datetime, date, timedelta
from backend.src.models import (
    Client, ClientCreateData, ClientStatus,
    Subscription, SubscriptionType, SubscriptionStatus, SubscriptionCreateData,
    Booking, BookingStatus, BookingCreateData
)

# --- Client Model Tests ---
def test_client_creation_valid():
    client = Client(
        name="Андрей",
        phone="+79991234567",
        telegram_id=123456,
        yoga_experience=True,
        intensity_preference="средняя",
        time_preference="утро"
    )
    assert client.name == "Андрей"
    assert client.phone == "+79991234567"
    assert client.status == ClientStatus.ACTIVE
    assert client.intensity_preference == "средняя"
    assert client.time_preference == "утро"

@pytest.mark.parametrize("phone", ["79991234567", "12345", "+7999-123-45-67"])
def test_client_invalid_phone(phone):
    with pytest.raises(ValueError):
        Client(
            name="Test",
            phone=phone,
            telegram_id=1,
            yoga_experience=False,
            intensity_preference="низкая",
            time_preference="вечер"
        )

@pytest.mark.parametrize("intensity", ["очень высокая", "", "medium"])
def test_client_invalid_intensity(intensity):
    with pytest.raises(ValueError):
        Client(
            name="Test",
            phone="+79991234567",
            telegram_id=1,
            yoga_experience=False,
            intensity_preference=intensity,
            time_preference="вечер"
        )

# --- Subscription Model Tests ---
def test_subscription_creation_valid():
    today = date.today()
    sub = Subscription(
        client_id="client1",
        type=SubscriptionType.PACKAGE_4,
        total_classes=4,
        used_classes=1,
        start_date=today,
        end_date=today + timedelta(days=30),
        status=SubscriptionStatus.ACTIVE,
        price=3200,
        payment_confirmed=True
    )
    assert sub.remaining_classes == 3
    assert sub.is_active
    assert not sub.is_expired
    assert not sub.is_exhausted

@pytest.mark.parametrize("used,total", [(5,4), (10,8)])
def test_subscription_used_classes_exceed(used, total):
    today = date.today()
    with pytest.raises(ValueError):
        Subscription(
            client_id="client1",
            type=SubscriptionType.PACKAGE_4,
            total_classes=total,
            used_classes=used,
            start_date=today,
            end_date=today + timedelta(days=30),
            status=SubscriptionStatus.ACTIVE,
            price=3200,
            payment_confirmed=True
        )

# --- Booking Model Tests ---
def test_booking_creation_valid():
    future = datetime.now() + timedelta(days=1)
    booking = Booking(
        client_id="client1",
        class_date=future,
        class_type="хатха",
        status=BookingStatus.SCHEDULED
    )
    assert booking.class_type == "хатха"
    assert booking.is_upcoming
    assert not booking.is_past
    assert booking.can_be_cancelled

@pytest.mark.parametrize("class_type", ["boxing", "", "йога"], ids=["boxing","empty","йога"])
def test_booking_invalid_class_type(class_type):
    future = datetime.now() + timedelta(days=1)
    with pytest.raises(ValueError):
        Booking(
            client_id="client1",
            class_date=future,
            class_type=class_type,
            status=BookingStatus.SCHEDULED
        )

def test_booking_past_date():
    past = datetime.now() - timedelta(days=1)
    with pytest.raises(ValueError):
        Booking(
            client_id="client1",
            class_date=past,
            class_type="хатха",
            status=BookingStatus.SCHEDULED
        ) 