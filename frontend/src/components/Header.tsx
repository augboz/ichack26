import { Camera, BookOpen } from "lucide-react";

interface HeaderProps {
  buildingName?: string;
  spaceName?: string;
  activeCameraCount?: number;
}

export function Header({ buildingName, spaceName, activeCameraCount }: HeaderProps) {
  return (
    <header className="flex items-center justify-between py-6">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-xl bg-primary/10 border border-primary/20">
          <BookOpen className="w-6 h-6 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            {spaceName || buildingName || "LibrarySpace"}
          </h1>
          <p className="text-sm text-muted-foreground">
            {buildingName && spaceName ? buildingName : "Imperial College Library"}
          </p>
        </div>
      </div>

      {activeCameraCount !== undefined && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-secondary/50 border border-border">
          <Camera className="w-4 h-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">
            {activeCameraCount} {activeCameraCount === 1 ? 'camera' : 'cameras'} active
          </span>
        </div>
      )}
    </header>
  );
}
