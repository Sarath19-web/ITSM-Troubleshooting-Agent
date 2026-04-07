import { useQuery } from "@tanstack/react-query";
import { getTrendingFaqs } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { TrendingUp } from "lucide-react";

export function TrendingFaqs() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["trending-faqs"],
    queryFn: getTrendingFaqs,
  });

  if (isLoading) {
    return (
      <div className="bg-card rounded-xl border border-border p-6">
        <Skeleton className="h-4 w-32 mb-4" />
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-8 w-full" />)}
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="bg-card rounded-xl border border-border p-6 text-center">
        <p className="text-sm text-muted-foreground">Failed to load trending FAQs</p>
        <button onClick={() => refetch()} className="mt-2 text-xs text-primary hover:underline">Retry</button>
      </div>
    );
  }

  const faqs = data.trending_faqs || [];

  return (
    <div className="bg-card rounded-xl border border-border p-6">
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp className="w-4 h-4 text-primary" />
        <h3 className="text-sm font-semibold">Trending FAQs</h3>
      </div>
      {faqs.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-4">No trending FAQs yet</p>
      ) : (
        <div className="space-y-2">
          {faqs.slice(0, 10).map((faq, i) => (
            <div key={i} className="flex items-start justify-between gap-2 text-sm py-1.5 border-b border-border last:border-0">
              <span className="truncate">{faq.question}</span>
              <span className="text-xs text-muted-foreground shrink-0">{faq.hit_count} hits</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
