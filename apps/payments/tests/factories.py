from __future__ import annotations

from decimal import Decimal

import factory

from apps.contests.tests.factories import ContestFactory
from apps.payments.models import EntryPayment, PaymentStatus
from apps.users.tests.factories import UserFactory


class PaidContestFactory(ContestFactory):
    entry_fee = Decimal("150.00")
    currency = "TJS"


class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EntryPayment
        skip_postgeneration_save = True

    contest = factory.SubFactory(PaidContestFactory)
    user = factory.SubFactory(UserFactory)
    amount = Decimal("150.00")
    currency = "TJS"
    status = PaymentStatus.AWAITING_RECEIPT
