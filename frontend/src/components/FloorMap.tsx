import { cn } from "@/lib/utils";

interface Seat {
  id: string;
  x: number;
  y: number;
  zone: string;
  occupied: boolean;
}

// Mock seat data - would come from CV backend
const seats: Seat[] = [
  // Tables 1-4 (left section)
  { id: "T1-1", x: 8, y: 20, zone: "Tables 1–4", occupied: false },
  { id: "T1-2", x: 14, y: 20, zone: "Tables 1–4", occupied: false },
  { id: "T1-3", x: 8, y: 28, zone: "Tables 1–4", occupied: true },
  { id: "T1-4", x: 14, y: 28, zone: "Tables 1–4", occupied: false },
  { id: "T2-1", x: 8, y: 40, zone: "Tables 1–4", occupied: false },
  { id: "T2-2", x: 14, y: 40, zone: "Tables 1–4", occupied: true },
  { id: "T2-3", x: 8, y: 48, zone: "Tables 1–4", occupied: false },
  { id: "T2-4", x: 14, y: 48, zone: "Tables 1–4", occupied: true },
  { id: "T3-1", x: 8, y: 60, zone: "Tables 1–4", occupied: false },
  { id: "T3-2", x: 14, y: 60, zone: "Tables 1–4", occupied: false },
  { id: "T3-3", x: 8, y: 68, zone: "Tables 1–4", occupied: true },
  { id: "T3-4", x: 14, y: 68, zone: "Tables 1–4", occupied: false },
  
  // Quiet Row (middle section)
  { id: "Q1", x: 38, y: 20, zone: "Quiet Row", occupied: true },
  { id: "Q2", x: 44, y: 20, zone: "Quiet Row", occupied: true },
  { id: "Q3", x: 50, y: 20, zone: "Quiet Row", occupied: true },
  { id: "Q4", x: 56, y: 20, zone: "Quiet Row", occupied: true },
  { id: "Q5", x: 62, y: 20, zone: "Quiet Row", occupied: true },
  { id: "Q6", x: 38, y: 28, zone: "Quiet Row", occupied: true },
  { id: "Q7", x: 44, y: 28, zone: "Quiet Row", occupied: false },
  { id: "Q8", x: 50, y: 28, zone: "Quiet Row", occupied: true },
  { id: "Q9", x: 56, y: 28, zone: "Quiet Row", occupied: false },
  { id: "Q10", x: 62, y: 28, zone: "Quiet Row", occupied: true },
  
  // Window Seats (right section)
  { id: "W1", x: 82, y: 20, zone: "Window Seats", occupied: false },
  { id: "W2", x: 88, y: 20, zone: "Window Seats", occupied: false },
  { id: "W3", x: 82, y: 32, zone: "Window Seats", occupied: true },
  { id: "W4", x: 88, y: 32, zone: "Window Seats", occupied: false },
  { id: "W5", x: 82, y: 44, zone: "Window Seats", occupied: false },
  { id: "W6", x: 88, y: 44, zone: "Window Seats", occupied: true },
  { id: "W7", x: 82, y: 56, zone: "Window Seats", occupied: false },
  { id: "W8", x: 88, y: 56, zone: "Window Seats", occupied: false },
];

function SeatMarker({ seat }: { seat: Seat }) {
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
      title={`${seat.id} - ${seat.occupied ? "Occupied" : "Available"}`}
    />
  );
}


function ZoneLabel({ label, x, y }: { label: string; x: number; y: number }) {
  return (
    <div
      className="absolute text-xs font-medium text-muted-foreground/70 whitespace-nowrap"
      style={{
        left: `${x}%`,
        top: `${y}%`,
        transform: "translate(-50%, -50%)",
      }}
    >
      {label}
    </div>
  );
}

export function FloorMap() {
  const freeCount = seats.filter((s) => !s.occupied).length;
  const occupiedCount = seats.filter((s) => s.occupied).length;

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

        {/* Zone areas */}
        <div
          className="absolute rounded-lg border border-success/20 bg-success/5"
          style={{ left: "3%", top: "10%", width: "22%", height: "80%" }}
        />
        <div
          className="absolute rounded-lg border border-warning/20 bg-warning/5"
          style={{ left: "30%", top: "10%", width: "40%", height: "35%" }}
        />
        <div
          className="absolute rounded-lg border border-primary/20 bg-primary/5"
          style={{ left: "75%", top: "10%", width: "22%", height: "80%" }}
        />

        {/* Zone labels */}
        <ZoneLabel label="Tables 1–4" x={14} y={85} />
        <ZoneLabel label="Quiet Row" x={50} y={50} />
        <ZoneLabel label="Window Seats" x={86} y={85} />

        {/* Window decoration on right side */}
        <div
          className="absolute right-0 top-0 bottom-0 w-1 bg-gradient-to-b from-primary/40 via-primary/20 to-primary/40"
        />

        {/* Entrance indicator */}
        <div className="absolute bottom-3 left-1/2 -translate-x-1/2">
  <div className="px-3 py-1 bg-card/90 backdrop-blur border border-border rounded-full text-xs text-muted-foreground shadow-sm">
    Entrance
  </div>
</div>


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
