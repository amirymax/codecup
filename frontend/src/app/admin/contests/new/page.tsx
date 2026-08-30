import { Navbar } from "@/components/Navbar";
import { ContestForm } from "@/components/admin/ContestForm";
import { requireAdmin } from "@/lib/adminGuard";

export default async function NewContestPage() {
  const user = await requireAdmin("/admin/contests/new");

  return (
    <div className="min-h-screen bg-ink text-text">
      <Navbar user={user} active="admin" />
      <div className="mx-auto max-w-[1180px] px-5 py-6 pb-25 sm:px-10 sm:py-10">
        <ContestForm />
      </div>
    </div>
  );
}
