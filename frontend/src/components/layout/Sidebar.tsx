import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  ClipboardList,
  Settings,
  Activity,
} from 'lucide-react';
import { cn } from '@/lib/utils';

const navGroups = [
  {
    label: 'Operations',
    items: [
      { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/work-orders', icon: ClipboardList, label: 'Work Orders' },
    ],
  },
  {
    label: 'System',
    items: [
      { to: '/sessions', icon: Activity, label: 'Sessions' },
      { to: '/admin', icon: Settings, label: 'Admin' },
    ],
  },
];

export function Sidebar() {
  return (
    <aside className="w-56 shrink-0 bg-card border-r border-border flex flex-col h-screen sticky top-0">
      <div className="p-4 border-b border-border">
        <h1 className="text-sm font-bold tracking-wide text-foreground">Battery Test Bench</h1>
        <p className="text-[10px] text-muted-foreground">Control System v2.0</p>
      </div>
      <nav className="flex-1 overflow-y-auto py-2">
        {navGroups.map(group => (
          <div key={group.label} className="mb-2">
            <p className="px-4 py-1 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
              {group.label}
            </p>
            {group.items.map(item => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-4 py-2 text-sm transition-colors duration-150',
                    isActive
                      ? 'bg-accent text-accent-foreground font-medium'
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent/50',
                  )
                }
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
    </aside>
  );
}
