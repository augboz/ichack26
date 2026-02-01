import { cn } from "@/lib/utils";
import { useState, useEffect } from "react";

interface Desk {
  desk_id: number;
  name: string;
  capacity: number;
  grid_x: number;
  grid_y: number;
  occupied: boolean;
  confidence: number;
  last_updated: string | null;
  sample_count: number;
}

interface SpaceData {
  space_id: number;
  grid_width: number;
  grid_height: number;
  desks: Desk[];
}

interface Seat {
  id: string;
  name: string;
  x: number;
  y: number;
  occupied: boolean;
  confidence: number;
}

function SeatMarker({ seat }: { seat: Seat }) {
  const confidencePercent = Math.round(seat.confidence * 100);
  const title = `${seat.name} - ${seat.occupied ? "Occupied" : "Available"}${
    seat.confidence > 0 ? ` (${confidencePercent}% confidence)` : ""
  }`;

  return (
    <div
      className={cn(
        "absolute w-4 h-4 rounded-full transition-all duration-300 cursor-pointer",
        "hover:scale-125 hover:z-10",
        seat.occupied
          ? "bg-destructive/80 shadow-[0_0_8px_hsl(var(--destructive)/0.5)]"
          : "bg-success shadow-[0_0_10px_hsl(var(--success)/0.45)]"
      )}
      style={{
        left: `${seat.x}%`,
        top: `${seat.y}%`,
        transform: "translate(-50%, -50%)",
      }}
      title={title}
    />
  );
}


export function FloorMap({ spaceId = 1 }: { spaceId?: number }) {
  const [seats, setSeats] = useState<Seat[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDesks = async () => {
      try {
        setLoading(true);
        const response = await fetch(`http://localhost:5000/api/spaces/${spaceId}/desks`);

        if (!response.ok) {
          throw new Error('Failed to fetch desk data');
        }

        const data: SpaceData = await response.json();

        // Convert grid coordinates to percentage positions
        // Add padding of 10% on each side for better visualization
        const padding = 10;
        const usableWidth = 100 - (padding * 2);
        const usableHeight = 100 - (padding * 2);

        const convertedSeats: Seat[] = data.desks.map((desk) => ({
          id: desk.desk_id.toString(),
          name: desk.name,
          x: padding + (desk.grid_x / Math.max(data.grid_width - 1, 1)) * usableWidth,
          y: padding + (desk.grid_y / Math.max(data.grid_height - 1, 1)) * usableHeight,
          occupied: desk.occupied,
          confidence: desk.confidence,
        }));

        setSeats(convertedSeats);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
        console.error('Error fetching desk data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDesks();

    // Poll for updates every 5 seconds
    const interval = setInterval(fetchDesks, 5000);

    return () => clearInterval(interval);
  }, [spaceId]);

  const freeCount = seats.filter((s) => !s.occupied).length;
  const occupiedCount = seats.filter((s) => s.occupied).length;

  if (loading && seats.length === 0) {
    return (
      <div className="rounded-2xl border border-border bg-card p-6 overflow-hidden">
        <div className="flex items-center justify-center h-64">
          <p className="text-muted-foreground">Loading floor plan...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-border bg-card p-6 overflow-hidden">
        <div className="flex items-center justify-center h-64">
          <p className="text-destructive">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-border bg-card p-6 overflow-hidden">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-foreground">Floor Plan</h2>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-success shadow-[0_0_6px_hsl(var(--success)/0.5)]" />
            <span className="text-muted-foreground">{freeCount} Free</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-destructive/80" />
            <span className="text-muted-foreground">{occupiedCount} Occupied</span>
          </div>
        </div>
      </div>

      {/* Map container */}
      <div className="relative w-full aspect-[2/1] bg-secondary/30 rounded-xl border border-border/50 overflow-hidden">
        {/* Grid pattern background */}
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: `
              linear-gradient(to right, hsl(var(--border)) 1px, transparent 1px),
              linear-gradient(to bottom, hsl(var(--border)) 1px, transparent 1px)
            `,
            backgroundSize: "20px 20px",
          }}
        />



        {/* Seat markers */}
        {seats.map((seat) => (
          <SeatMarker key={seat.id} seat={seat} />
        ))}
      </div>

      <p className="text-xs text-muted-foreground mt-3 text-center">
        Tap a seat to see details • Green = available • Red = occupied
      </p>
    </div>
  );
}
