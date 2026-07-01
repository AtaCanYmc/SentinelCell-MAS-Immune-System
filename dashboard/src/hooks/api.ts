export const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
  const getCsrfToken = () => {
    const match = document.cookie.match(new RegExp('(^| )sentinel_csrf=([^;]+)'));
    return match ? match[2] : '';
  };

  const headers = new Headers(options.headers || {});
  const csrfToken = getCsrfToken();
  if (csrfToken && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(options.method?.toUpperCase() || '')) {
    headers.set('X-CSRF-Token', csrfToken);
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'same-origin',
  });

  if (response.status === 401) {
    if (!window.location.pathname.includes('/login')) {
      window.location.href = '/login';
    }
  }

  return response;
};
