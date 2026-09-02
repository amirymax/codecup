"""Правила участия в платных контестах."""

from __future__ import annotations

from apps.contests.models import Contest

from .models import EntryPayment, PaymentSettings, PaymentStatus


def can_submit(contest: Contest, user) -> bool:
    """Бесплатный контест открыт всем, платный — только с принятым взносом."""
    if not contest.is_paid:
        return True
    if not user or not user.is_authenticated:
        return False
    return EntryPayment.objects.filter(
        contest=contest, user=user, status=PaymentStatus.ACCEPTED
    ).exists()


def get_or_create_payment(contest: Contest, user) -> EntryPayment:
    """Заявка на участие. Сумма фиксируется в момент создания."""
    payment, _ = EntryPayment.objects.get_or_create(
        contest=contest,
        user=user,
        defaults={"amount": contest.entry_fee, "currency": contest.currency},
    )
    return payment


def participation_state(contest: Contest, user) -> dict:
    payment = None
    if user and user.is_authenticated:
        payment = EntryPayment.objects.filter(contest=contest, user=user).first()

    return {
        "is_paid": contest.is_paid,
        "entry_fee": contest.entry_fee,
        "currency": contest.currency,
        "requisites": PaymentSettings.load().effective_requisites if contest.is_paid else "",
        "can_submit": can_submit(contest, user),
        "payment": payment,
    }
