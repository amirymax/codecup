import { notFound } from "next/navigation";

import { Navbar } from "@/components/Navbar";
import { ContestForm } from "@/components/admin/ContestForm";
import { requireAdmin } from "@/lib/adminGuard";
import { getAdminContest } from "@/lib/api/server";
import { ApiRequestError } from "@/lib/api/errors";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function EditContestPage({ params }: Props) {
  const { id } = await params;
  const user = await requireAdmin(`/admin/contests/${id}`);

  const contest = await getAdminContest(id).catch((error) => {
    if (error instanceof ApiRequestError && error.status === 404) notFound();
    throw error;
  });

  return (
    <div className="min-h-screen bg-ink text-text">
      <Navbar user={user} active="admin" />
      <div className="mx-auto max-w-[1180px] px-5 py-6 pb-25 sm:px-10 sm:py-10">
        <ContestForm existing={contest} />
      </div>
    </div>
  );
}
