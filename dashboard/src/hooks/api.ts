export const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
  const response = await fetch(url, {
    ...options,
    credentials: 'same-origin',
  });

  if (response.status === 401) {
    if (!window.location.pathname.includes('/login')) {
      window.location.href = '/login';
    }
  }

  return response;
};
