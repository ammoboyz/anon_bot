from typing import Optional
from aiogram.filters.callback_data import CallbackData


class CreatePaymentCallbackFactory(CallbackData, prefix="payment"):
    user_id: int
    pay_code: str
    method_name: str
    days: int = 0


class PremiumCallbackFactory(CallbackData, prefix="premium"):
    product: str
    amount: int
    days: int = 0

    callback_back: Optional[str] = None


class InterestsCallbackFactory(CallbackData, prefix="profile"):
    action: str

    interest: str
    is_active: bool = False
