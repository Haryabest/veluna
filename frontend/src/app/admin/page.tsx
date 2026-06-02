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
    <div className="px-4 pt-6 max-w-lg mx-auto space-y-6">
      <h1 className="text-xl font-bold">Admin Panel</h1>

      <div className="grid grid-cols-2 gap-3">
        {isLoading
          ? Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-lg" />)
          : [
              { label: "Users", value: stats?.total_users },
              { label: "Messages", value: stats?.total_messages },
              { label: "Generations", value: stats?.total_generations },
              { label: "Revenue", value: stats?.total_revenue_gems },
            ].map((stat) => (
              <Card key={stat.label}>
                <p className="text-text-muted text-xs">{stat.label}</p>
                <p className="text-2xl font-bold mt-1">{stat.value ?? 0}</p>
              </Card>
            ))}
      </div>

      <section className="space-y-2">
        <h2 className="text-sm font-semibold text-text-secondary">Management</h2>
        {["Characters", "Users", "Transactions", "Pricing", "Analytics"].map((item) => (
          <Card key={item} className="flex items-center justify-between cursor-pointer hover:bg-bg-elevated">
            <span className="text-sm">{item}</span>
            <span className="text-text-muted">→</span>
          </Card>
        ))}
      </section>
    </div>
  );
}
