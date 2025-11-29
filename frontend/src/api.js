const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";



export async function apiFetch(endpoint, options = {}) {
  const token = localStorage.getItem("access_token");
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = {
    ...(options.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };

  return fetch(url, {
    ...options,
    headers
  });
}

