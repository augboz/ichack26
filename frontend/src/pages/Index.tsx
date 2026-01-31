import { Header } from "@/components/Header";
import { FloorMap } from "@/components/FloorMap";
import { StatsCard } from "@/components/StatsCard";
import { ZoneCard } from "@/components/ZoneCard";
import { useStatus } from "@/hooks/use-status";
import { Armchair, BookOpen, Sun } from "lucide-react";

type ZoneUI = {
  id: string;
  name: string;
  free: number;
  capacity: number;
  icon: React.ReactNode;
};

function getZoneState(
  free: number,
  capacity: number
): "available" | "moderate" | "full" {
  const ratio = free / Math.max(capacity, 1);
  if (ratio > 0.5) return "available";
  if (ratio > 0.2) return "moderate";
  return "full";
}

function iconForZone(name: string) {
  if (name === "Tables 1–4") return <Armchair className="w-4 h-4" />;
  if (name === "Quiet Row") return <BookOpen className="w-4 h-4" />;
  return <Sun className="w-4 h-4" />;
}

// Demo fallback data (used if backend is down or still building)
const fallbackZones: ZoneUI[] = [
  {
    id: "Tables_1_4",
    name: "Tables 1–4",
    free: 8,
    capacity: 12,
    icon: <Armchair className="w-4 h-4" />,
  },
  {
    id: "Quiet_Row",
    name: "Quiet Row",
    free: 2,
    capacity: 10,
    icon: <BookOpen className="w-4 h-4" />,
  },
  {
    id: "Window_Seats",
    name: "Window Seats",
    free: 6,
    capacity: 8,
    icon: <Sun className="w-4 h-4" />,
  },
];

const Index = () => {
  const { data, error } = useStatus(1000);

  const zones: ZoneUI[] = data?.zones
    ? data.zones.map((z) => ({
        id: String(z.id),
        name: z.name,
        free: z.free,
        capacity: z.capacity,
        icon: iconForZone(z.name),
      }))
    : fallbackZones;

  const totalFree =
    typeof data?.total_free === "number"
      ? data.total_free
      : zones.reduce((sum, z) => sum + z.free, 0);

  const totalCapacity =
    typeof data?.total_capacity === "number"
      ? data.total_capacity
      : zones.reduce((sum, z) => sum + z.capacity, 0);

  const lastUpdated = data
    ? `Updated ${new Date().toLocaleTimeString()}`
    : "Updated just now";

  return (
    <div className="min-h-screen bg-background">
      {/* Subtle background pattern */}
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/5 via-transparent to-transparent pointer-events-none" />

      <div className="relative max-w-4xl mx-auto px-6 pb-12">
        <Header />

        {error && (
          <div className="mt-4 rounded-xl border border-border bg-card p-3 text-sm text-muted-foreground">
            Backend not reachable. Showing demo data.
            <span className="ml-2 opacity-70">({error})</span>
          </div>
        )}

        <main className="space-y-8">
          {/* Hero stats */}
          <section
            className="animate-fade-in"
            style={{ animationDelay: "0.1s" }}
          >
            <StatsCard
              freeSeats={totalFree}
              totalSeats={totalCapacity}
              lastUpdated={lastUpdated}
            />
          </section>

          {/* Zone cards */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-foreground">Zones</h2>
              <span className="text-sm text-muted-foreground">
                {zones.length} areas monitored
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {zones.map((zone, index) => (
                <div
                  key={zone.id}
                  className="animate-fade-in"
                  style={{ animationDelay: `${0.2 + index * 0.1}s` }}
                >
                  <ZoneCard
                    name={zone.name}
                    free={zone.free}
                    capacity={zone.capacity}
                    state={getZoneState(zone.free, zone.capacity)}
                    icon={zone.icon}
                  />
                </div>
              ))}
            </div>
          </section>

          {/* Floor map */}
          <section
            className="animate-fade-in"
            style={{ animationDelay: "0.5s" }}
          >
          <FloorMap seats={data?.seats ?? []} />
          </section>

          {/* Footer info */}
          <footer className="pt-8 border-t border-border">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
              <p>Powered by computer vision • ICHack 2026</p>
              <p>Data refreshes every 1 second</p>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
};

export default Index;
