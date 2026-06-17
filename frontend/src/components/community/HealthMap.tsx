"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import "leaflet/dist/leaflet.css";
import type { Resident } from "@/types";
import RiskBadge from "@/components/ui/RiskBadge";

interface HealthMapProps {
  residents: Resident[];
  filter: string;
}

export default function HealthMap({ residents, filter }: HealthMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<unknown>(null);
  const [selected, setSelected] = useState<Resident | null>(null);

  const filtered = useMemo(
    () => (filter === "全部" ? residents : residents.filter((r) => r.status === filter)),
    [residents, filter]
  );

  useEffect(() => {
    if (!mapRef.current || typeof window === "undefined") return;

    const container = mapRef.current;
    let removed = false;

    const init = async () => {
      const L = (await import("leaflet")).default;
      await import("leaflet.heat");

      if (removed) return;

      // 清理旧地图
      if (mapInstanceRef.current) {
        (mapInstanceRef.current as { remove: () => void }).remove();
      }

      const avgLat = filtered.reduce((s, r) => s + r.lat, 0) / (filtered.length || 1);
      const avgLng = filtered.reduce((s, r) => s + r.lng, 0) / (filtered.length || 1);

      const map = L.map(container).setView([avgLat, avgLng], 15);
      mapInstanceRef.current = map;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 19,
      }).addTo(map);

      // 等底图加载完成后再添加热力图（避免 canvas 高度为 0）
      map.whenReady(() => {
        if (removed) return;
        map.invalidateSize();

        const heatData = filtered.map((r) => {
          const weight = r.status === "高危" ? 80 : r.status === "中风险" ? 40 : 5;
          return [r.lat, r.lng, weight] as [number, number, number];
        });

        try {
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (L as any).heatLayer(heatData, {
            minOpacity: 0.3,
            radius: 30,
            blur: 15,
            gradient: { 0.2: "blue", 0.4: "lime", 0.6: "yellow", 0.8: "orange", 1.0: "red" },
          }).addTo(map);
        } catch (e) {
          console.warn("热力图加载失败，跳过:", e);
        }
      });

      // 散点标记
      filtered.forEach((r) => {
        const color =
          r.status === "高危" ? "#EF4444" : r.status === "中风险" ? "#F59E0B" : "#22C55E";
        const radius = r.is_current_user ? 10 : r.status === "高危" ? 8 : 6;

        const marker = L.circleMarker([r.lat, r.lng], {
          radius,
          fillColor: color,
          fillOpacity: r.is_current_user ? 0.8 : 0.6,
          color: r.is_current_user ? "#0078FF" : color,
          weight: r.is_current_user ? 3 : 2,
        }).addTo(map);

        marker.on("click", () => setSelected(r));
      });
    };

    init();

    return () => {
      removed = true;
      if (mapInstanceRef.current) {
        (mapInstanceRef.current as { remove: () => void }).remove();
        mapInstanceRef.current = null;
      }
    };
  }, [filtered]);

  return (
    <div className="relative">
      <div ref={mapRef} className="h-[500px] w-full rounded-xl border border-gray-200" />

      {selected && (
        <div className="absolute right-3 top-3 z-[1000] w-64 rounded-xl border border-gray-200 bg-white p-4 shadow-lg">
          <div className="mb-2 flex items-center justify-between">
            <h4 className="font-semibold text-gray-900">{selected.name}</h4>
            <button
              onClick={() => setSelected(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <RiskBadge level={selected.status} size="sm" />
          <div className="mt-3 space-y-1 text-sm text-gray-600">
            <p>血压：{selected.systolic}/{selected.diastolic} mmHg</p>
            <p>更新：{selected.last_update}</p>
          </div>
        </div>
      )}
    </div>
  );
}
