import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Users, MapPin, Search, Loader2, Clock, Calendar } from "lucide-react";

interface SpaceResult {
  building_id: number;
  building_name: string;
  building_address: string;
  space_id: number;
  space_name: string;
  distance_km: number;
  available_seats?: number;
  predicted_available_seats?: number;
  recommended_desks: string[];
  desk_ids: number[];
  is_prediction?: boolean;
  prediction_confidence?: number;
  total_historical_samples?: number;
  predicted_for?: string;
}

export default function FindSpace() {
  const navigate = useNavigate();
  const [groupSize, setGroupSize] = useState(1);
  const [location, setLocation] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SpaceResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [scheduleLater, setScheduleLater] = useState(false);
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedTime, setSelectedTime] = useState("");

  const handleUseCurrentLocation = () => {
    setLocation("");
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const lat = position.coords.latitude;
          const lng = position.coords.longitude;
          setLocation(`${lat.toFixed(6)}, ${lng.toFixed(6)}`);
        },
        () => {
          setError("Could not get your location. Please enter it manually.");
        }
      );
    } else {
      setError("Geolocation is not supported by your browser.");
    }
  };

  const handleFindSpace = async () => {
    setError(null);
    setResult(null);

    // Parse location
    let lat, lng;
    if (location.includes(",")) {
      const parts = location.split(",").map(s => s.trim());
      lat = parseFloat(parts[0]);
      lng = parseFloat(parts[1]);
    } else {
      setError("Please enter location as 'latitude, longitude' or use current location");
      return;
    }

    if (isNaN(lat) || isNaN(lng)) {
      setError("Invalid location coordinates");
      return;
    }

    setLoading(true);

    try {
      let url: string;

      if (scheduleLater && selectedDate && selectedTime) {
        // Use prediction endpoint for future times
        const datetime = `${selectedDate}T${selectedTime}`;
        url = `http://localhost:5000/api/find-space/predict?group_size=${groupSize}&latitude=${lat}&longitude=${lng}&datetime=${datetime}`;
      } else {
        // Use real-time endpoint
        url = `http://localhost:5000/api/find-space?group_size=${groupSize}&latitude=${lat}&longitude=${lng}`;
      }

      const response = await fetch(url);

      if (response.ok) {
        const data = await response.json();
        setResult(data);
      } else {
        const errorData = await response.json();
        setError(errorData.error || "No available spaces found");
      }
    } catch (err) {
      setError("Failed to search for spaces. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/5 via-transparent to-transparent pointer-events-none" />

      <div className="relative max-w-2xl mx-auto px-6 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">Find a Study Space</h1>
          <p className="text-muted-foreground mt-2">
            Find the nearest available study space for you or your group
          </p>
        </div>

        <div className="space-y-6">
          {/* Group Size */}
          <div className="rounded-2xl border border-border bg-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Users className="w-5 h-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">Group Size</h2>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => setGroupSize(Math.max(1, groupSize - 1))}
                className="w-10 h-10 rounded-lg bg-secondary hover:bg-secondary/80 flex items-center justify-center font-semibold"
                disabled={groupSize <= 1}
              >
                -
              </button>
              <div className="flex-1 text-center">
                <div className="text-3xl font-bold text-foreground">{groupSize}</div>
                <div className="text-sm text-muted-foreground">
                  {groupSize === 1 ? "person" : "people"}
                </div>
              </div>
              <button
                onClick={() => setGroupSize(groupSize + 1)}
                className="w-10 h-10 rounded-lg bg-secondary hover:bg-secondary/80 flex items-center justify-center font-semibold"
              >
                +
              </button>
            </div>
            {groupSize > 1 && (
              <p className="text-xs text-muted-foreground mt-4">
                We'll find {groupSize} adjacent seats for your group
              </p>
            )}
          </div>

          {/* Location */}
          <div className="rounded-2xl border border-border bg-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <MapPin className="w-5 h-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">Your Location</h2>
            </div>
            <div className="space-y-3">
              <button
                onClick={handleUseCurrentLocation}
                className="w-full px-4 py-3 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 font-medium"
              >
                Use Current Location
              </button>
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-border"></div>
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-card px-2 text-muted-foreground">Or</span>
                </div>
              </div>
              <input
                type="text"
                placeholder="Enter coordinates (e.g., 51.4988, -0.1749)"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full px-4 py-3 rounded-lg bg-secondary border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>

          {/* When to Visit */}
          <div className="rounded-2xl border border-border bg-card p-6">
            <div className="flex items-center gap-2 mb-4">
              <Clock className="w-5 h-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">When</h2>
            </div>
            <div className="space-y-4">
              {/* Toggle */}
              <div className="flex gap-2">
                <button
                  onClick={() => setScheduleLater(false)}
                  className={`flex-1 px-4 py-3 rounded-lg font-medium transition-colors ${
                    !scheduleLater
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary text-muted-foreground hover:bg-secondary/80"
                  }`}
                >
                  Now
                </button>
                <button
                  onClick={() => setScheduleLater(true)}
                  className={`flex-1 px-4 py-3 rounded-lg font-medium transition-colors ${
                    scheduleLater
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary text-muted-foreground hover:bg-secondary/80"
                  }`}
                >
                  Schedule Later
                </button>
              </div>

              {/* Date/Time Picker */}
              {scheduleLater && (
                <div className="space-y-3 animate-fade-in">
                  <div className="flex gap-3">
                    <div className="flex-1">
                      <label className="text-sm text-muted-foreground mb-1 block">Date</label>
                      <input
                        type="date"
                        value={selectedDate}
                        onChange={(e) => setSelectedDate(e.target.value)}
                        min={new Date().toISOString().split('T')[0]}
                        className="w-full px-4 py-3 rounded-lg bg-secondary border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                    <div className="flex-1">
                      <label className="text-sm text-muted-foreground mb-1 block">Time</label>
                      <input
                        type="time"
                        value={selectedTime}
                        onChange={(e) => setSelectedTime(e.target.value)}
                        className="w-full px-4 py-3 rounded-lg bg-secondary border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    <Calendar className="w-3 h-3 inline mr-1" />
                    Predictions are based on historical occupancy patterns
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Search Button */}
          <button
            onClick={handleFindSpace}
            disabled={!location || loading || (scheduleLater && (!selectedDate || !selectedTime))}
            className="w-full px-6 py-4 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 font-semibold text-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                {scheduleLater ? "Predicting..." : "Searching..."}
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
                {scheduleLater ? "Predict Availability" : "Find Space"}
              </>
            )}
          </button>

          {/* Error */}
          {error && (
            <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-4">
              <p className="text-destructive text-sm">{error}</p>
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="rounded-2xl border border-border bg-card p-6 animate-fade-in">
              <div className="flex items-center gap-2 mb-4">
                <h2 className="text-xl font-bold text-foreground">
                  {result.is_prediction ? "Predicted Available Space" : "Found Available Space!"}
                </h2>
                {result.is_prediction && (
                  <span className="px-2 py-1 rounded-full bg-amber-500/20 text-amber-500 text-xs font-medium">
                    Prediction
                  </span>
                )}
              </div>

              {/* Prediction Info */}
              {result.is_prediction && result.predicted_for && (
                <div className="mb-4 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <div className="flex items-center gap-2 text-sm">
                    <Calendar className="w-4 h-4 text-amber-500" />
                    <span className="text-foreground">
                      Predicted for: {new Date(result.predicted_for).toLocaleString()}
                    </span>
                  </div>
                  {result.prediction_confidence !== undefined && (
                    <div className="mt-2 text-xs text-muted-foreground">
                      Confidence: {Math.round(result.prediction_confidence * 100)}%
                      {result.total_historical_samples && ` (based on ${result.total_historical_samples} historical samples)`}
                    </div>
                  )}
                </div>
              )}

              <div className="space-y-3">
                <div>
                  <div className="text-sm text-muted-foreground">Building</div>
                  <div className="text-lg font-semibold text-foreground">
                    {result.building_name}
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {result.building_address}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Space</div>
                  <div className="text-lg font-semibold text-foreground">
                    {result.space_name}
                  </div>
                </div>
                <div className="flex gap-4">
                  <div>
                    <div className="text-sm text-muted-foreground">Distance</div>
                    <div className="text-lg font-semibold text-foreground">
                      {result.distance_km} km
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">
                      {result.is_prediction ? "Predicted Available" : "Available Seats"}
                    </div>
                    <div className="text-lg font-semibold text-foreground">
                      {result.predicted_available_seats ?? result.available_seats}
                    </div>
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-2">
                    Recommended Desks
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {result.recommended_desks.map((desk, idx) => (
                      <div
                        key={idx}
                        className="px-3 py-1 rounded-full bg-success/20 text-success text-sm font-medium"
                      >
                        {desk}
                      </div>
                    ))}
                  </div>
                </div>
                <button
                  onClick={() => navigate(`/building/${result.building_id}`)}
                  className="w-full mt-4 px-4 py-3 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 font-medium"
                >
                  View Details
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
