import { useEffect, useRef, useCallback, useState } from 'react';
import type { WsMessage, StationStatus } from '@/types';

const WS_PATH = '/api/ws/live';
const RECONNECT_BASE = 1000;
const RECONNECT_MAX = 30000;
const PING_INTERVAL = 25000;

export function useWebSocket() {
  const [stations, setStations] = useState<StationStatus[]>([]);
  const [awaitingTasks, setAwaitingTasks] = useState<Map<number, { id: number; task_number: number; label: string; step_type: string }>>(new Map());
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectDelay = useRef(RECONNECT_BASE);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const pingTimer = useRef<ReturnType<typeof setInterval>>(undefined);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}${WS_PATH}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      reconnectDelay.current = RECONNECT_BASE;
      pingTimer.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send('ping');
      }, PING_INTERVAL);
    };

    ws.onmessage = (event) => {
      if (event.data === 'pong') return;
      try {
        const msg: WsMessage = JSON.parse(event.data);
        if (msg.type === 'initial' || msg.type === 'update') {
          setStations(msg.data);
        } else if (msg.type === 'task_awaiting_input') {
          setAwaitingTasks(prev => {
            const next = new Map(prev);
            next.set(msg.station_id, {
              id: msg.task.id,
              task_number: msg.task.task_number,
              label: msg.task.label,
              step_type: msg.task.step_type,
            });
            return next;
          });
        }
      } catch {
        /* ignore parse errors */
      }
    };

    ws.onclose = () => {
      setConnected(false);
      if (pingTimer.current) clearInterval(pingTimer.current);
      reconnectTimer.current = setTimeout(() => {
        reconnectDelay.current = Math.min(reconnectDelay.current * 2, RECONNECT_MAX);
        connect();
      }, reconnectDelay.current);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      if (pingTimer.current) clearInterval(pingTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { stations, awaitingTasks, connected };
}
