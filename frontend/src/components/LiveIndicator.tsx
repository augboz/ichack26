export function LiveIndicator() {
  return (
    <div className="flex items-center gap-2">
      <span className="relative flex h-2.5 w-2.5">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-success"></span>
      </span>
      <span className="text-sm font-medium text-success">Live</span>
    </div>
  );
}
