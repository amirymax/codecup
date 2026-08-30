import { redirect } from "next/navigation";

import { getCurrentUser } from "@/lib/api/server";
import type { User } from "@/lib/api/types";

/**
 * Пускает в админку только сотрудников.
 *
 * Права проверяет и backend, но без этой проверки участник увидел бы
 * каркас админки с пустыми данными вместо честного отказа.
 */
export async function requireAdmin(next: string): Promise<User> {
  const user = await getCurrentUser();
  if (!user) redirect(`/login?next=${encodeURIComponent(next)}`);
  if (!user.is_admin) redirect("/");
  return user;
}
