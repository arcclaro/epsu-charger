import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { StationContext } from '@/hooks/useStations';
import { useWebSocket } from '@/hooks/useWebSocket';
import { TooltipProvider } from '@/components/ui/tooltip';

export function AppShell() {
  const ws = useWebSocket();

  return (
    <StationContext.Provider value={ws}>
      <TooltipProvider>
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <div className="flex flex-col flex-1 min-w-0">
            <Header />
            <main className="flex-1 overflow-y-auto p-4">
              <Outlet />
            </main>
          </div>
        </div>
      </TooltipProvider>
    </StationContext.Provider>
  );
}
