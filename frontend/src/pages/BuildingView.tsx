import { Header } from "@/components/Header";
import { FloorMap } from "@/components/FloorMap";
import { StatsCard } from "@/components/StatsCard";
import { ZoneCard } from "@/components/ZoneCard";
import { CameraCard } from "@/components/CameraCard";
import { OccupancyHeatmap } from "@/components/OccupancyHeatmap";
import { Armchair, BookOpen, Sun, ArrowLeft } from "lucide-react";
import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";

interface Zone {
  name: string;
  free: number;
  occupied: number;
  capacity: number;
  free_percentage: number;
}

interface Space {
  space_id: number;
  name: string;
  total_capacity: number;
  grid_width: number;
  grid_height: number;
}

interface Camera {
  camera_id: number;
  name: string;
  stream_url: string | null;
  resolution_x: number;
  resolution_y: number;
  is_active: boolean;
  desk_count: number;
}

interface Building {
  building_id: number;
  name: string;
  latitude: number;
  longitude: number;
  address: string;
  total_capacity: number;
  free_seats: number;
  occupied_seats: number;
  occupancy_percentage: number;
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

export default function BuildingView() {
  const { buildingId } = useParams<{ buildingId: string }>();
  const navigate = useNavigate();
  const [building, setBuilding] = useState<Building | null>(null);
  const [spaces, setSpaces] = useState<Space[]>([]);
  const [selectedSpaceId, setSelectedSpaceId] = useState<number | null>(null);
  const [zones, setZones] = useState<Zone[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch building information
  useEffect(() => {
    const fetchBuilding = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/buildings');
        if (response.ok) {
          const buildings = await response.json();
          const currentBuilding = buildings.find((b: Building) => b.building_id === Number(buildingId));
          if (currentBuilding) {
            setBuilding(currentBuilding);
          }
        }
      } catch (error) {
        console.error('Error fetching building:', error);
      }
    };

    if (buildingId) {
      fetchBuilding();
    }
  }, [buildingId]);

  // Fetch spaces for this building
  useEffect(() => {
    const fetchSpaces = async () => {
      try {
        const response = await fetch(`http://localhost:5000/api/buildings/${buildingId}/spaces`);
        if (response.ok) {
          const data = await response.json();
          setSpaces(data);
          // Default to first space
          if (data.length > 0 && !selectedSpaceId) {
            setSelectedSpaceId(data[0].space_id);
          }
        }
      } catch (error) {
        console.error('Error fetching spaces:', error);
      } finally {
        setLoading(false);
      }
    };

    if (buildingId) {
      fetchSpaces();
    }
  }, [buildingId]);

  // Fetch zones for selected space
  useEffect(() => {
    const fetchZones = async () => {
      if (!selectedSpaceId) return;

      try {
        const response = await fetch(`http://localhost:5000/api/spaces/${selectedSpaceId}/zones`);
        if (response.ok) {
          const data = await response.json();
          setZones(data);
        }
      } catch (error) {
        console.error('Error fetching zones:', error);
      }
    };

    fetchZones();

    // Poll for updates every 5 seconds
    const interval = setInterval(fetchZones, 5000);
    return () => clearInterval(interval);
  }, [selectedSpaceId]);

  // Fetch cameras for selected space
  useEffect(() => {
    const fetchCameras = async () => {
      if (!selectedSpaceId) return;

      try {
        const response = await fetch(`http://localhost:5000/api/spaces/${selectedSpaceId}/cameras`);
        if (response.ok) {
          const data = await response.json();
          setCameras(data);
        }
      } catch (error) {
        console.error('Error fetching cameras:', error);
      }
    };

    fetchCameras();
  }, [selectedSpaceId]);

  const totalFree = zones.reduce((sum, zone) => sum + zone.free, 0);
  const totalCapacity = zones.reduce((sum, zone) => sum + zone.capacity, 0);
  const selectedSpace = spaces.find(s => s.space_id === selectedSpaceId);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Subtle background pattern */}
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/5 via-transparent to-transparent pointer-events-none" />

      <div className="relative max-w-4xl mx-auto px-6 pb-12">
        {/* Back button and space selector */}
        <div className="pt-6 mb-4 flex items-center justify-between gap-4">
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Back to Campus Map</span>
          </button>

          {spaces.length > 1 && (
            <select
              value={selectedSpaceId || ''}
              onChange={(e) => setSelectedSpaceId(Number(e.target.value))}
              className="px-4 py-2 rounded-lg bg-card border border-border text-foreground"
            >
              {spaces.map((space) => (
                <option key={space.space_id} value={space.space_id}>
                  {space.name}
                </option>
              ))}
            </select>
          )}
        </div>

        <Header
          buildingName={building?.name}
          spaceName={selectedSpace?.name}
          activeCameraCount={cameras.filter(c => c.is_active).length}
        />

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

          {/* Cameras */}
          {cameras.length > 0 && (
            <section>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-foreground">Cameras</h2>
                <span className="text-sm text-muted-foreground">
                  {cameras.filter(c => c.is_active).length} active
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {cameras.map((camera) => (
                  <CameraCard
                    key={camera.camera_id}
                    name={camera.name}
                    resolution={`${camera.resolution_x}×${camera.resolution_y}`}
                    deskCount={camera.desk_count}
                    isActive={camera.is_active}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Floor map */}
          {selectedSpaceId && (
            <section className="animate-fade-in" style={{ animationDelay: "0.5s" }}>
              <FloorMap spaceId={selectedSpaceId} />
            </section>
          )}

          {/* Occupancy Heatmap */}
          {selectedSpaceId && (
            <section className="animate-fade-in" style={{ animationDelay: "0.6s" }}>
              <OccupancyHeatmap spaceId={selectedSpaceId} />
            </section>
          )}

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
}
