import { Video } from "lucide-react";

interface CameraCardProps {
  name: string;
  resolution: string;
  deskCount: number;
  isActive: boolean;
}

export function CameraCard({ name, resolution, deskCount, isActive }: CameraCardProps) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${isActive ? 'bg-success/10' : 'bg-muted'}`}>
            <Video className={`w-5 h-5 ${isActive ? 'text-success' : 'text-muted-foreground'}`} />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">{name}</h3>
            <p className="text-sm text-muted-foreground">{resolution}</p>
          </div>
        </div>
        <div className={`px-2 py-1 rounded-full text-xs font-medium ${
          isActive
            ? 'bg-success/10 text-success'
            : 'bg-muted text-muted-foreground'
        }`}>
          {isActive ? 'Active' : 'Inactive'}
        </div>
      </div>
      <div className="mt-3 text-sm text-muted-foreground">
        Monitoring {deskCount} {deskCount === 1 ? 'desk' : 'desks'}
      </div>
    </div>
  );
}
