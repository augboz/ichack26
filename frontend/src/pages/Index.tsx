import { Header } from "@/components/Header";
import { FloorMap } from "@/components/FloorMap";
import { StatsCard } from "@/components/StatsCard";
import { ZoneCard } from "@/components/ZoneCard";
import { Armchair, BookOpen, Sun } from "lucide-react";
import { useState, useEffect } from "react";

interface Zone {
  name: string;
  free: number;
  occupied: number;
  capacity: number;
  free_percentage: number;
}

const zoneIcons: Record<string, JSX.Element> = {
  "Tables 1–4": <Armchair className="w-4 h-4" />,
  "Quiet Row": <BookOpen className="w-4 h-4" />,
  "Window Seats": <Sun className="w-4 h-4" />,
};

function getZoneState(free: number, capacity: number): "available" | "moderate" | "full" {
  const ratio = free / capacity;
  if (ratio > 0.5) return "available";
  if (ratio > 0.2) return "moderate";
  return "full";
}

const Index = () => {
  const [zones, setZones] = useState<Zone[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchZones = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/spaces/1/zones');
        if (response.ok) {
          const data = await response.json();
          setZones(data);
        }
      } catch (error) {
        console.error('Error fetching zones:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchZones();

    // Poll for updates every 5 seconds
    const interval = setInterval(fetchZones, 5000);
    return () => clearInterval(interval);
  }, []);

  const totalFree = zones.reduce((sum, zone) => sum + zone.free, 0);
  const totalCapacity = zones.reduce((sum, zone) => sum + zone.capacity, 0);

  return (
    <div className="min-h-screen bg-background">
      {/* Subtle background pattern */}
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/5 via-transparent to-transparent pointer-events-none" />
      
      <div className="relative max-w-4xl mx-auto px-6 pb-12">
        <Header />
        
        <main className="space-y-8">
          {/* Hero stats */}
          <section className="animate-fade-in" style={{ animationDelay: "0.1s" }}>
            <StatsCard 
              freeSeats={totalFree} 
              totalSeats={totalCapacity}
              lastUpdated="Updated just now"
            />
          </section>

          {/* Zone cards */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-foreground">Zones</h2>
              <span className="text-sm text-muted-foreground">
                {loading ? 'Loading...' : `${zones.length} areas monitored`}
              </span>
            </div>

            {loading ? (
              <div className="text-center py-8 text-muted-foreground">Loading zone data...</div>
            ) : zones.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">No zones configured</div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {zones.map((zone, index) => (
                  <div
                    key={zone.name}
                    className="animate-fade-in"
                    style={{ animationDelay: `${0.2 + index * 0.1}s` }}
                  >
                    <ZoneCard
                      name={zone.name}
                      free={zone.free}
                      capacity={zone.capacity}
                      state={getZoneState(zone.free, zone.capacity)}
                      icon={zoneIcons[zone.name] || <Armchair className="w-4 h-4" />}
                    />
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Floor map */}
          <section className="animate-fade-in" style={{ animationDelay: "0.5s" }}>
            <FloorMap />
          </section>

          {/* Footer info */}
          <footer className="pt-8 border-t border-border">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
              <p>Powered by computer vision • ICHack 2026</p>
              <p>Data refreshes every 5 seconds</p>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
};

export default Index;
