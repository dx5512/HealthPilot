"use client";

import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import type { VitalsInput } from "@/types";

interface VitalsFormProps {
  onSubmit: (data: VitalsInput) => void;
  loading: boolean;
}

export default function VitalsForm({ onSubmit, loading }: VitalsFormProps) {
  const { user } = useAuth();
  const [form, setForm] = useState<VitalsInput>({
    user_id: user?.user_id || "",
    age: 65,
    systolic: 120,
    diastolic: 80,
    heart_rate: 75,
    spo2: 98,
    height: 170,
    weight: 65,
  });

  const set = (key: keyof VitalsInput, value: string) => {
    setForm((prev) => ({
      ...prev,
      [key]: key === "user_id" ? value : Number(value),
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(form);
  };

  const fields: {
    key: keyof VitalsInput;
    label: string;
    unit: string;
    min: number;
    max: number;
    step?: number;
  }[] = [
    { key: "age", label: "年龄", unit: "岁", min: 0, max: 120 },
    { key: "systolic", label: "收缩压", unit: "mmHg", min: 60, max: 250 },
    { key: "diastolic", label: "舒张压", unit: "mmHg", min: 40, max: 150 },
    { key: "heart_rate", label: "心率", unit: "bpm", min: 40, max: 200 },
    { key: "spo2", label: "血氧", unit: "%", min: 70, max: 100 },
    { key: "height", label: "身高", unit: "cm", min: 100, max: 250 },
    { key: "weight", label: "体重", unit: "kg", min: 30, max: 150, step: 0.1 },
  ];

  return (
    <form onSubmit={handleSubmit} className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold text-gray-900">📝 录入居民体征</h2>

      <div className="mb-4">
        <label className="mb-1 block text-sm font-medium text-gray-700">居民 ID</label>
        <input
          type="text"
          value={form.user_id}
          onChange={(e) => set("user_id", e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-primary focus:ring-1 focus:ring-primary"
          required
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {fields.map((f) => (
          <div key={f.key}>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              {f.label} <span className="text-gray-400">({f.unit})</span>
            </label>
            <input
              type="number"
              value={form[f.key]}
              onChange={(e) => set(f.key, e.target.value)}
              min={f.min}
              max={f.max}
              step={f.step || 1}
              className="w-full rounded-lg border border-gray-300 px-4 py-2.5 text-sm focus:border-primary focus:ring-1 focus:ring-primary"
              required
            />
          </div>
        ))}
      </div>

      <button
        type="submit"
        disabled={loading}
        className="mt-6 w-full rounded-lg bg-primary px-6 py-3 text-base font-semibold text-white transition-colors hover:bg-primary-dark disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "🤖 分析中，请稍候..." : "🚀 开始智能分析"}
      </button>
    </form>
  );
}
