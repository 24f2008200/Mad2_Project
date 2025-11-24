export function useSearchEndpoint() {
  const endpointMap = {
    user: "/api/admin/users",
    reservation: "/api/admin/search?type=bookings",
    lot: "/api/admin/search?type=lots",
    reminder: "/api/admin/reminders/logs",
  };

  const buildEndpoint = (type, by, value) => {
    const base = endpointMap[type];
    if (!base) return null;
    return `${base}?search_by=${by}&value=${encodeURIComponent(value)}`;
  };

  return { buildEndpoint };
}
 