import { createFileRoute } from "@tanstack/react-router";
import { AppSidebar } from "@/components/AppSidebar";
import { KPICards } from "@/components/dashboard/KPICards";
import { CategoryChart } from "@/components/dashboard/CategoryChart";
import { PriorityChart } from "@/components/dashboard/PriorityChart";
import { TicketTable } from "@/components/dashboard/TicketTable";
import { CacheStatsCard } from "@/components/dashboard/CacheStatsCard";
import { TrendingFaqs } from "@/components/dashboard/TrendingFaqs";

export const Route = createFileRoute("/dashboard")({
  component: DashboardPage,
});

function DashboardPage() {
  return (
    <div className="flex min-h-screen w-full">
      <AppSidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="p-6 space-y-6 max-w-[1400px]">
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <KPICards />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <CategoryChart />
            <PriorityChart />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <CacheStatsCard />
            <TrendingFaqs />
          </div>
          <TicketTable />
        </div>
      </main>
    </div>
  );
}
