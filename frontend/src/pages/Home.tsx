import { useState } from "react";
import { Map, Search } from "lucide-react";
import CampusMap from "./CampusMap";
import FindSpace from "./FindSpace";

export default function Home() {
  const [activeTab, setActiveTab] = useState<"map" | "find">("map");

  return (
    <div className="min-h-screen">
      {/* Tab Navigation */}
      <div className="fixed top-0 left-0 right-0 z-[1001] bg-slate-900/95 backdrop-blur-sm border-b border-slate-700">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab("map")}
              className={`flex-1 px-6 py-3 rounded-lg font-semibold transition-all flex items-center justify-center gap-2 ${
                activeTab === "map"
                  ? "bg-primary text-primary-foreground"
                  : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              <Map className="w-5 h-5" />
              Map View
            </button>
            <button
              onClick={() => setActiveTab("find")}
              className={`flex-1 px-6 py-3 rounded-lg font-semibold transition-all flex items-center justify-center gap-2 ${
                activeTab === "find"
                  ? "bg-primary text-primary-foreground"
                  : "bg-slate-800 text-slate-300 hover:bg-slate-700"
              }`}
            >
              <Search className="w-5 h-5" />
              Find Space
            </button>
          </div>
        </div>
      </div>

      {/* Tab Content */}
      <div className="pt-20">
        {activeTab === "map" ? <CampusMap /> : <FindSpace />}
      </div>
    </div>
  );
}
