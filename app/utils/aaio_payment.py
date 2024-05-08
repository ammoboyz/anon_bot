import os

from aaio import AAIO
from app.utils.config import Settings
from settings import MERCHANT_ID, SECRET_KEY

async def create_payment_url(
        order_id: str,
        amount: int,
        config: Settings
    ) -> str:
    client = AAIO(
        merchant_id=MERCHANT_ID,
        secret=SECRET_KEY,
        api_key=config.payments.api_key
    )

    url = client.create_payment(
        amount=amount,
        order_id=order_id,
        description="Оплата в анон чате."
    )

    return url
