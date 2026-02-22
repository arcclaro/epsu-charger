export function formatVoltage(mv: number): string {
  return `${(mv / 1000).toFixed(2)} V`;
}

export function formatCurrent(ma: number): string {
  if (Math.abs(ma) >= 1000) {
    return `${(ma / 1000).toFixed(2)} A`;
  }
  return `${ma.toFixed(0)} mA`;
}

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export function formatTemp(c: number): string {
  return `${c.toFixed(1)} °C`;
}

export function formatCapacity(ah: number): string {
  return `${ah.toFixed(2)} Ah`;
}

export function formatResistance(mohm: number): string {
  return `${mohm.toFixed(2)} MOhm`;
}

export function formatWeight(kg: number): string {
  return `${kg.toFixed(2)} kg`;
}
