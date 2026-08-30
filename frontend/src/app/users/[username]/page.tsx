import { notFound } from "next/navigation";

import { Navbar } from "@/components/Navbar";
import { ProfileView } from "@/components/profile/ProfileView";
import { ApiRequestError } from "@/lib/api/errors";
import { getCurrentUser, getPublicProfile } from "@/lib/api/server";

interface Props {
  params: Promise<{ username: string }>;
}

/** Публичный профиль участника: черновики сюда не попадают. */
export default async function PublicProfilePage({ params }: Props) {
  const { username } = await params;
  const viewer = await getCurrentUser();

  const profile = await getPublicProfile(username).catch((error) => {
    if (error instanceof ApiRequestError && error.status === 404) notFound();
    throw error;
  });

  return (
    <div className="min-h-screen bg-ink text-text">
      <Navbar user={viewer} />
      <ProfileView
        username={profile.user.display_name}
        joinedAt={profile.user.created_at}
        submissionsCount={profile.submissions_count}
        winsCount={profile.wins_count}
        submissions={profile.submissions}
      />
    </div>
  );
}
