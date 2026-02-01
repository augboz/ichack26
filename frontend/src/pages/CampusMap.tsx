import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

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

// Create colored marker icons based on occupancy
function getMarkerColor(occupancyPercentage: number): string {
  if (occupancyPercentage < 40) return '#10b981'; // Green - lots of free seats
  if (occupancyPercentage < 70) return '#f59e0b'; // Amber - moderate
  return '#ef4444'; // Red - almost full
}

function createColoredIcon(color: string) {
  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background-color: ${color};
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        cursor: pointer;
      "></div>
    `,
    iconSize: [30, 30],
    iconAnchor: [15, 15],
  });
}

export default function CampusMap() {
  const [buildings, setBuildings] = useState<Building[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchBuildings = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/buildings');
        if (response.ok) {
          const data = await response.json();
          setBuildings(data);
        }
      } catch (error) {
        console.error('Error fetching buildings:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchBuildings();
    // Poll for updates every 10 seconds
    const interval = setInterval(fetchBuildings, 10000);
    return () => clearInterval(interval);
  }, []);

  // Calculate center from buildings or use default
  const center: [number, number] = buildings.length > 0
    ? [
        buildings.reduce((sum, b) => sum + b.latitude, 0) / buildings.length,
        buildings.reduce((sum, b) => sum + b.longitude, 0) / buildings.length
      ]
    : [51.505, -0.09]; // Default center (London)

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <p className="text-white text-xl">Loading campus map...</p>
      </div>
    );
  }

  return (
    <div className="relative w-full h-[calc(100vh-80px)]">
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-[1000] bg-gradient-to-b from-slate-900/95 to-transparent p-6">
        <h1 className="text-3xl font-bold text-white mb-2">Campus Occupancy Map</h1>
        <p className="text-slate-300">Click on a building to view details</p>

        {/* Legend */}
        <div className="mt-4 flex gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-[#10b981] border-2 border-white"></div>
            <span className="text-white">&lt;40% Full</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-[#f59e0b] border-2 border-white"></div>
            <span className="text-white">40-70% Full</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-[#ef4444] border-2 border-white"></div>
            <span className="text-white">&gt;70% Full</span>
          </div>
        </div>
      </div>

      {/* Map */}
      <MapContainer
        center={center}
        zoom={17}
        className="w-full h-full"
        style={{ background: '#0f172a' }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />

        {buildings.map((building) => (
          <Marker
            key={building.building_id}
            position={[building.latitude, building.longitude]}
            icon={createColoredIcon(getMarkerColor(building.occupancy_percentage))}
            eventHandlers={{
              click: () => navigate(`/building/${building.building_id}`)
            }}
          >
            <Popup>
              <div className="text-sm">
                <h3 className="font-bold text-base mb-1">{building.name}</h3>
                <p className="text-gray-600 mb-2">{building.address}</p>
                <div className="space-y-1">
                  <p><strong>Free:</strong> {building.free_seats} seats</p>
                  <p><strong>Occupied:</strong> {building.occupied_seats} seats</p>
                  <p><strong>Total:</strong> {building.total_capacity} seats</p>
                  <p className="mt-2 font-semibold">
                    {building.occupancy_percentage}% occupied
                  </p>
                </div>
                <button
                  onClick={() => navigate(`/building/${building.building_id}`)}
                  className="mt-3 w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
                >
                  View Details
                </button>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
