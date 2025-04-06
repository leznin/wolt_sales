import { useState, useEffect, useCallback } from 'react';

const useFetch = (fetchFunction, dependencies = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await fetchFunction();
      if (result !== null) {
        setData(result);
      }
    } catch (err) {
      console.error('Ошибка в useFetch:', err);
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [fetchFunction]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    let isMounted = true;
    
    const execute = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const result = await fetchFunction();
        if (isMounted && result !== null) {
          setData(result);
        }
      } catch (err) {
        console.error('Ошибка в эффекте useFetch:', err);
        if (isMounted) {
          setError(err);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    execute();

    return () => {
      isMounted = false;
    };
  }, [fetchFunction, ...dependencies]);

  return { data, loading, error, refetch: fetchData };
};

export default useFetch;