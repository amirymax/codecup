import Link from "next/link";

import { ArrowLeftIcon } from "@/components/Icons";
import { Navbar } from "@/components/Navbar";
import { PaymentRow } from "@/components/admin/PaymentRow";
import { requireAdmin } from "@/lib/adminGuard";
import { getAdminPayments } from "@/lib/api/server";
import { admin, payments as t } from "@/messages/ru";

interface Props {
  searchParams: Promise<{ status?: string }>;
}

export default async function AdminPaymentsPage({ searchParams }: Props) {
  const { status } = await searchParams;
  const user = await requireAdmin("/admin/payments");
  const list = await getAdminPayments(status ? { status } : {});

  return (
    <div className="min-h-screen bg-ink text-text">
      <Navbar user={user} active="admin" />

      <div className="mx-auto max-w-[1180px] px-5 py-6 pb-25 sm:px-10 sm:py-10">
        <Link
          href="/admin"
          className="mb-5 inline-flex items-center gap-1.5 text-[13.5px] text-muted-2
                     no-underline hover:text-text-2"
        >
          <ArrowLeftIcon />
          {admin.dashboard}
        </Link>

        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-2xl font-extrabold tracking-tight">{t.title}</h1>
          <div className="flex gap-2">
            <Filter current={status} value={undefined} label="Все" />
            <Filter current={status} value="pending" label={t.pending} />
            <Filter current={status} value="accepted" label={t.accepted} />
            <Filter current={status} value="rejected" label={t.rejected} />
          </div>
        </div>

        {list.results.length === 0 ? (
          <p className="rounded-xl border border-dashed border-line-2 bg-surface px-5 py-12 text-center text-sm text-muted-2">
            {t.empty}
          </p>
        ) : (
          <div className="overflow-hidden rounded-xl border border-line bg-surface">
            {list.results.map((payment) => (
              <PaymentRow key={payment.id} payment={payment} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function Filter({
  current,
  value,
  label,
}: {
  current: string | undefined;
  value: string | undefined;
  label: string;
}) {
  const active = current === value;
  return (
    <Link
      href={value ? `/admin/payments?status=${value}` : "/admin/payments"}
      className={`rounded-full px-3.5 py-1.5 text-[12.5px] font-semibold no-underline ${
        active ? "bg-surface-4 text-text" : "text-muted-2 hover:text-text"
      }`}
    >
      {label}
    </Link>
  );
}
