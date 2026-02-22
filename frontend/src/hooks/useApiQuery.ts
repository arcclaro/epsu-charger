import { useState, useEffect, useCallback, useRef } from 'react';

interface QueryState<T> {
  data: T | null;
  error: Error | null;
  isLoading: boolean;
}

export function useApiQuery<T>(fetcher: () => Promise<T>, deps: unknown[] = []) {
  const [state, setState] = useState<QueryState<T>>({ data: null, error: null, isLoading: true });
  const mountedRef = useRef(true);

  const refetch = useCallback(() => {
    setState(s => ({ ...s, isLoading: true, error: null }));
    fetcher()
      .then(data => { if (mountedRef.current) setState({ data, error: null, isLoading: false }); })
      .catch(error => { if (mountedRef.current) setState({ data: null, error, isLoading: false }); });
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    mountedRef.current = true;
    refetch();
    return () => { mountedRef.current = false; };
  }, [refetch]);

  return { ...state, refetch };
}
