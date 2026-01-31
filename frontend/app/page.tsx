export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <h1 className="text-3xl font-bold mb-6">LibSpace</h1>

      {/* Top metric */}
      <div className="bg-white rounded-xl shadow p-6 mb-8">
        <p className="text-gray-500">Free seats now</p>
        <p className="text-6xl font-bold text-green-600">27</p>
        <p className="text-sm text-gray-400 mt-2">Updated just now</p>
      </div>

      {/* Zones */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <ZoneCard name="Tables 1–4" free={8} capacity={12} state="green" />
        <ZoneCard name="Quiet Row" free={2} capacity={10} state="red" />
        <ZoneCard name="Window Seats" free={6} capacity={8} state="yellow" />
      </div>
    </main>
  );
}

function ZoneCard({
  name,
  free,
  capacity,
  state,
}: {
  name: string;
  free: number;
  capacity: number;
  state: "green" | "yellow" | "red";
}) {
  const colors = {
    green: "border-green-500 bg-green-50 text-green-700",
    yellow: "border-yellow-500 bg-yellow-50 text-yellow-700",
    red: "border-red-500 bg-red-50 text-red-700",
  };

  return (
    <div
      className={`border-l-8 rounded-xl bg-white p-4 shadow ${colors[state]}`}
    >
      <h2 className="font-semibold">{name}</h2>
      <p className="text-2xl font-bold mt-2">
        {free} / {capacity}
      </p>
      <p className="text-sm">seats free</p>
    </div>
  );
}
