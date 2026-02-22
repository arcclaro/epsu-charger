import { useLocation, Link } from 'react-router-dom';
import { Bell } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { useStations } from '@/hooks/useStations';

const routeNames: Record<string, string> = {
  '': 'Dashboard',
  'work-orders': 'Work Orders',
  'customers': 'Customers',
  'battery-profiles': 'Battery Profiles',
  'tech-pubs': 'Tech Pubs',
  'recipes': 'Recipes',
  'calibration': 'Calibration',
  'admin': 'Admin',
  'sessions': 'Sessions',
  'station': 'Station',
  'jobs': 'Job',
};

export function Header() {
  const location = useLocation();
  const { awaitingTasks, connected } = useStations();

  const segments = location.pathname.split('/').filter(Boolean);
  const breadcrumbs = segments.map((seg, i) => {
    const path = '/' + segments.slice(0, i + 1).join('/');
    const label = routeNames[seg] ?? (seg.startsWith('OT-') ? seg : isNaN(Number(seg)) ? seg : `#${seg}`);
    return { path, label };
  });

  const awaitingCount = awaitingTasks.size;

  return (
    <header className="h-10 border-b border-border bg-card flex items-center px-4 gap-4 shrink-0">
      <nav className="flex items-center gap-1 text-sm text-muted-foreground flex-1 min-w-0">
        <Link to="/" className="hover:text-foreground transition-colors">Home</Link>
        {breadcrumbs.map(bc => (
          <span key={bc.path} className="flex items-center gap-1">
            <span className="text-border">/</span>
            <Link to={bc.path} className="hover:text-foreground transition-colors truncate">
              {bc.label}
            </Link>
          </span>
        ))}
      </nav>

      <div className="flex items-center gap-3">
        <div className={`h-2 w-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}
          title={connected ? 'WebSocket connected' : 'Disconnected'} />

        {awaitingCount > 0 && (
          <Link to="/station/1/awaiting" className="relative">
            <Bell className="h-4 w-4 text-amber-400" />
            <Badge
              variant="destructive"
              className="absolute -top-2 -right-2 h-4 min-w-4 px-1 text-[10px] flex items-center justify-center"
            >
              {awaitingCount}
            </Badge>
          </Link>
        )}
      </div>
    </header>
  );
}
