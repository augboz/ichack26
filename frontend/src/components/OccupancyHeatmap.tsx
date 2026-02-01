import { useState, useEffect } from "react";

interface HeatmapData {
  space_id: number;
  total_capacity: number;
  days_analyzed: number | string;
  heatmap: number[][];
  day_labels: string[];
  hour_labels: string[];
}

interface OccupancyHeatmapProps {
  spaceId: number;
}

function getColorForOccupancy(percentage: number): string {
  if (percentage === 0) return 'bg-muted';
  if (percentage < 20) return 'bg-success/20';
  if (percentage < 40) return 'bg-success/40';
  if (percentage < 60) return 'bg-yellow-500/40';
  if (percentage < 80) return 'bg-orange-500/50';
  return 'bg-destructive/60';
}

export function OccupancyHeatmap({ spaceId }: OccupancyHeatmapProps) {
  const [heatmapData, setHeatmapData] = useState<HeatmapData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHeatmap = async () => {
      try {
        setLoading(true);
        const response = await fetch(`http://localhost:5000/api/spaces/${spaceId}/heatmap`);

        if (!response.ok) {
          throw new Error('Failed to fetch heatmap data');
        }

        const data: HeatmapData = await response.json();
        setHeatmapData(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
        console.error('Error fetching heatmap:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchHeatmap();
  }, [spaceId]);

  if (loading) {
    return (
      <div className="rounded-2xl border border-border bg-card p-6">
        <div className="flex items-center justify-center h-64">
          <p className="text-muted-foreground">Loading heatmap...</p>
        </div>
      </div>
    );
  }

  if (error || !heatmapData) {
    return (
      <div className="rounded-2xl border border-border bg-card p-6">
        <div className="flex items-center justify-center h-64">
          <p className="text-destructive">Error: {error || 'No data available'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-border bg-card p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Weekly Occupancy Heatmap</h2>
          <p className="text-sm text-muted-foreground mt-1">
            {heatmapData.days_analyzed === 'all'
              ? 'Average occupancy from all available data'
              : `Average occupancy over the last ${heatmapData.days_analyzed} days`}
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-muted-foreground">Low</span>
          <div className="flex gap-1">
            <div className="w-4 h-4 rounded bg-success/20"></div>
            <div className="w-4 h-4 rounded bg-success/40"></div>
            <div className="w-4 h-4 rounded bg-yellow-500/40"></div>
            <div className="w-4 h-4 rounded bg-orange-500/50"></div>
            <div className="w-4 h-4 rounded bg-destructive/60"></div>
          </div>
          <span className="text-muted-foreground">High</span>
        </div>
      </div>

      {/* Heatmap grid */}
      <div className="overflow-x-auto">
        <div className="inline-block min-w-full">
          {/* Hour labels */}
          <div className="flex mb-2">
            <div className="w-12 flex-shrink-0"></div>
            <div className="flex-1 flex">
              {heatmapData.hour_labels.map((hour, idx) => (
                idx % 3 === 0 ? (
                  <div
                    key={idx}
                    className="flex-1 text-center text-xs text-muted-foreground"
                    style={{ minWidth: '24px' }}
                  >
                    {hour.slice(0, 2)}
                  </div>
                ) : (
                  <div key={idx} className="flex-1" style={{ minWidth: '24px' }}></div>
                )
              ))}
            </div>
          </div>

          {/* Heatmap rows */}
          {heatmapData.heatmap.map((dayData, dayIdx) => (
            <div key={dayIdx} className="flex items-center mb-1">
              <div className="w-12 flex-shrink-0 text-xs text-muted-foreground font-medium">
                {heatmapData.day_labels[dayIdx]}
              </div>
              <div className="flex-1 flex gap-1">
                {dayData.map((occupancy, hourIdx) => (
                  <div
                    key={hourIdx}
                    className={`flex-1 h-6 rounded transition-all hover:scale-110 hover:z-10 cursor-pointer ${getColorForOccupancy(occupancy)}`}
                    style={{ minWidth: '24px' }}
                    title={`${heatmapData.day_labels[dayIdx]} ${heatmapData.hour_labels[hourIdx]}: ${occupancy}% occupied`}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <p className="text-xs text-muted-foreground mt-4 text-center">
        Hover over cells to see detailed occupancy percentages
      </p>
    </div>
  );
}
