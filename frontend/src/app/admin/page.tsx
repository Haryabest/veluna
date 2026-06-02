"use client";

import { useQuery } from "@tanstack/react-query";
import { adminService } from "@/services/api";
import { Card } from "@/components/shared/Card";
import { Skeleton } from "@/components/shared/Skeleton";
import { useUserStore } from "@/store/user-store";
import { QUERY_KEYS } from "@/lib/constants";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function AdminPage() {
  const { user } = useUserStore();
  const router = useRouter();

  useEffect(() => {
    if (user && user.role !== "admin") router.replace("/");
  }, [user, router]);

  const { data: stats, isLoading } = useQuery({
    queryKey: QUERY_KEYS.adminStats,
    queryFn: () => adminService.getStats(),
    enabled: user?.role === "admin",
  });

  if (!user || user.role !== "admin") return null;

  return (
    <div className="mx-auto max-w-lg space-y-6 px-4 pb-28 pt-6">
      <h1 className="text-xl font-bold">Админ-панель</h1>

      <div className="grid grid-cols-2 gap-3">
        {isLoading
          ? Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-2xl" />)
          : [
              { label: "Пользователи", value: stats?.total_users },
              { label: "Сообщения", value: stats?.total_messages },
              { label: "Генерации", value: stats?.total_generations },
              { label: "Доход (гемы)", value: stats?.total_revenue_gems },
            ].map((stat) => (
              <Card key={stat.label}>
                <p className="text-xs text-text-muted">{stat.label}</p>
                <p className="mt-1 text-2xl font-bold">{stat.value ?? 0}</p>
              </Card>
            ))}
      </div>

      <section className="space-y-2">
        <h2 className="text-sm font-semibold text-text-secondary">Управление</h2>
        {["Персонажи", "Пользователи", "Транзакции", "Цены", "Аналитика"].map((item) => (
          <Card key={item} className="flex cursor-pointer items-center justify-between hover:bg-bg-elevated/50">
            <span className="text-sm">{item}</span>
            <span className="text-text-muted">→</span>
          </Card>
        ))}
      </section>
    </div>
  );
}
