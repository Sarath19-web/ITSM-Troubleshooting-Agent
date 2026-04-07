import { useQuery } from "@tanstack/react-query";
import { getCacheStats } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { Database } from "lucide-react";

export function CacheStatsCard() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["cache-stats"],
    queryFn: getCacheStats,
  });

  if (isLoading) {
    return (
      <div className="bg-card rounded-xl border border-border p-6">
        <Skeleton className="h-4 w-32 mb-4" />
        <Skeleton className="h-20 w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="bg-card rounded-xl border border-border p-6 text-center">
        <p className="text-sm text-muted-foreground">Failed to load cache stats</p>
        <button onClick={() => refetch()} className="mt-2 text-xs text-primary hover:underline">Retry</button>
      </div>
    );
  }

  const hitRate = data.total_hits > 0 && data.total_entries > 0
    ? ((data.total_hits / (data.total_hits + data.total_entries)) * 100).toFixed(1)
    : "0";

  return (
    <div className="bg-card rounded-xl border border-border p-6">
      <div className="flex items-center gap-2 mb-4">
        <Database className="w-4 h-4 text-primary" />
        <h3 className="text-sm font-semibold">FAQ Cache</h3>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div>
          <p className="text-xs text-muted-foreground">Entries</p>
          <p className="text-2xl font-bold">{data.total_entries}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Total Hits</p>
          <p className="text-2xl font-bold">{data.total_hits}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Hit Rate</p>
          <p className="text-2xl font-bold">{hitRate}%</p>
        </div>
      </div>
    </div>
  );
}
