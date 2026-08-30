import { redirect } from "next/navigation";

import { Navbar } from "@/components/Navbar";
import { ProfileView } from "@/components/profile/ProfileView";
import { getCurrentUser, getMySubmissions } from "@/lib/api/server";

/** Свой профиль. В отличие от публичного, показывает и черновики. */
export default async function ProfilePage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login?next=/profile");

  const submissions = await getMySubmissions();
  const wins = submissions.results.filter((item) => item.display_status === "winner").length;
  const counted = submissions.results.filter((item) => item.display_status !== "draft").length;

  return (
    <div className="min-h-screen bg-ink text-text">
      <Navbar user={user} active="profile" />
      <ProfileView
        username={user.display_name}
        joinedAt={user.created_at}
        submissionsCount={counted}
        winsCount={wins}
        submissions={submissions.results}
        isOwn
      />
    </div>
  );
}
