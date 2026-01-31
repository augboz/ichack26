import { Users, Armchair } from "lucide-react";

type ZoneState = "available" | "moderate" | "full";

interface ZoneCardProps {
  name: string;
  free: number;
  capacity: number;
  state: ZoneState;
  icon?: React.ReactNode;
}

const stateConfig = {
  available: {
    border: "border-success/50",
    bg: "bg-success/5",
    glow: "glow-success",
    text: "text-success",
    badge: "bg-success/20 text-success",
    label: "Available",
  },
  moderate: {
    border: "border-warning/50",
    bg: "bg-warning/5",
    glow: "glow-warning",
    text: "text-warning",
    badge: "bg-warning/20 text-warning",
    label: "Filling up",
  },
  full: {
    border: "border-destructive/50",
    bg: "bg-destructive/5",
    glow: "glow-danger",
    text: "text-destructive",
    badge: "bg-destructive/20 text-destructive",
    label: "Almost full",
  },
};

export function ZoneCard({ name, free, capacity, state, icon }: ZoneCardProps) {
  const config = stateConfig[state];
  const percentage = Math.round((free / capacity) * 100);

  return (
    <div
      className={`
        relative overflow-hidden rounded-xl border ${config.border} ${config.bg}
        p-5 transition-all duration-300 hover:scale-[1.02] hover:${config.glow}
        backdrop-blur-sm group
      `}
    >
      {/* Background gradient effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-card/80 to-transparent pointer-events-none" />
      
      {/* Content */}
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className={`p-2 rounded-lg ${config.bg} ${config.text}`}>
              {icon || <Armchair className="w-4 h-4" />}
            </div>
            <h3 className="font-semibold text-foreground">{name}</h3>
          </div>
          <span className={`text-xs font-medium px-2 py-1 rounded-full ${config.badge}`}>
            {config.label}
          </span>
        </div>

        {/* Stats */}
        <div className="flex items-end justify-between">
          <div>
            <p className={`text-3xl font-bold ${config.text}`}>{free}</p>
            <p className="text-sm text-muted-foreground">of {capacity} seats free</p>
          </div>
          
          {/* Mini progress ring */}
          <div className="relative w-12 h-12">
            <svg className="w-12 h-12 -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-secondary"
                stroke="currentColor"
                strokeWidth="3"
                fill="none"
                d="M18 2.0845
                  a 15.9155 15.9155 0 0 1 0 31.831
                  a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className={config.text}
                stroke="currentColor"
                strokeWidth="3"
                strokeLinecap="round"
                fill="none"
                strokeDasharray={`${percentage}, 100`}
                d="M18 2.0845
                  a 15.9155 15.9155 0 0 1 0 31.831
                  a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <span className={`absolute inset-0 flex items-center justify-center text-xs font-bold ${config.text}`}>
              {percentage}%
            </span>
          </div>
        </div>
      </div>

      {/* Animated border glow on hover */}
      <div className={`
        absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300
        ${state === 'available' ? 'shadow-[inset_0_0_20px_hsl(var(--success)/0.1)]' : ''}
        ${state === 'moderate' ? 'shadow-[inset_0_0_20px_hsl(var(--warning)/0.1)]' : ''}
        ${state === 'full' ? 'shadow-[inset_0_0_20px_hsl(var(--destructive)/0.1)]' : ''}
        pointer-events-none
      `} />
    </div>
  );
}
