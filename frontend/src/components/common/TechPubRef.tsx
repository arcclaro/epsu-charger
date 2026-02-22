import { formatTechPubRef } from '@/lib/formatters';

interface TechPubRefProps {
  cmm?: string;
  revision?: string;
  ata?: string;
  date?: string;
  className?: string;
}

export function TechPubRef({ cmm, revision, ata, date, className }: TechPubRefProps) {
  const text = formatTechPubRef(cmm, revision, ata, date);
  if (!text) return null;
  return <span className={className ?? 'text-xs text-muted-foreground font-mono'}>{text}</span>;
}
