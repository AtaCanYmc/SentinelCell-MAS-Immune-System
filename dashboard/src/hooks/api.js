export const fetchWithAuth = async (url, options = {}) => {
  const token = localStorage.getItem('sentinel_api_key') || '';
  const headers = {
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    if (!window.location.pathname.includes('/login')) {
      window.location.href = '/login';
    }
  }

  return response;
};
