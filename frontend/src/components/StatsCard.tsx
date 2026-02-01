import { LiveIndicator } from "./LiveIndicator";

interface StatsCardProps {
  freeSeats: number;
  totalSeats: number;
  lastUpdated: string;
}

export function StatsCard({ freeSeats, totalSeats, lastUpdated }: StatsCardProps) {
  const percentage = Math.round((freeSeats / totalSeats) * 100);
  
  return (
    <div className="relative overflow-hidden rounded-2xl border border-border bg-card p-8">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-success/5 via-transparent to-transparent pointer-events-none" />
      
      {/* Decorative elements */}
      <div className="absolute -right-8 -top-8 w-32 h-32 bg-success/10 rounded-full blur-3xl" />
      <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-primary/5 rounded-full blur-2xl" />
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-muted-foreground text-sm font-medium mb-1">Free seats now</p>
            <LiveIndicator />
          </div>
          <div className="text-right">
            <p className="text-muted-foreground text-xs">{lastUpdated}</p>
          </div>
        </div>
        
        <div className="flex items-end gap-4">
          <div className="flex items-baseline gap-2">
            <span className="text-7xl font-bold text-gradient animate-float">{freeSeats}</span>
            <span className="text-2xl text-muted-foreground font-medium">/ {totalSeats}</span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-6">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-muted-foreground">Overall availability</span>
            <span className="text-success font-medium">{percentage}%</span>
          </div>
          <div className="h-2 bg-secondary rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-success to-emerald-400 rounded-full transition-all duration-500"
              style={{ width: `${percentage}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
