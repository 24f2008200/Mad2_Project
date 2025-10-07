const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

export async function apiFetch(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultHeaders = { "Content-Type": "application/json" };
  return fetch(url, {
    headers: { ...defaultHeaders, ...(options.headers || {}) },
    ...options,
  });
}


// const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

// export async function apiFetch(endpoint, options = {}) {
//   const url = `${API_BASE_URL}${endpoint}`;
//   const defaultHeaders = { "Content-Type": "application/json" };

//   // custom flag: skipDateConversion
//   const { doDateConversion, ...fetchOptions } = options;
//   if (!doDateConversion) {
//     return fetch(url, {
//       headers: { ...defaultHeaders, ...(fetchOptions.headers || {}) },
//       ...fetchOptions,
//     });
//   } else {
//     const res = await fetch(url, {
//       headers: { ...defaultHeaders, ...(fetchOptions.headers || {}) },
//       ...fetchOptions,
//     });

//     if (!res.ok) {
//       throw new Error(`API error: ${res.status}`);
//     }

//     const data = await res.json();

//     return convertTimeStringsToDates(data);
//   }
// }

// function convertTimeStringsToDates(data) {
//   if (Array.isArray(data)) {
//     return data.map(convertRow);
//   } else if (data && typeof data === "object") {
//     return convertRow(data);
//   }
//   return data;
// }

// function convertRow(row) {
//   const newRow = { ...row };
//   for (const key in newRow) {
//     const val = newRow[key];
//     if (
//       val &&
//       typeof val === "string" &&
//       key.toLowerCase().includes("time")
//     ) {
//       const parsed = new Date(val);
//       if (!isNaN(parsed)) {
//         newRow[key] = convert(parsed);
//       }
//     }
//   }
//   return newRow;
// }


// function convert(value) {
//   const d = String(value.getDate()).padStart(2, '0');
//   const m = String(value.getMonth() + 1).padStart(2, '0');
//   const y = value.getFullYear();
//   const h = String(value.getHours()).padStart(2, '0');
//   const min = String(value.getMinutes()).padStart(2, '0');
//   return `${d}-${m}-${y} ${h}:${min}`;
// }

