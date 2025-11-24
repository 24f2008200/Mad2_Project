// src/js/apiClient.js
import { getCommonParams } from '@/searchParams'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:5000") + "/api";

function getToken() {
    return localStorage.getItem("access_token") || null;
}

async function request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const commonParams = getCommonParams();
    // console.log('Retrieved Common Params:', commonParams);
    const queryString = new URLSearchParams(
        Object.fromEntries(
            Object.entries(commonParams).filter(([k, v]) => v !== null && v !== "")
        )
    ).toString();

    // console.log('Common Params:', queryString);
    const finalUrl = queryString ? `${url}?${queryString}` : url;

    // console.log('API Request URL new :', finalUrl);
    const headers = {
        "Content-Type": "application/json",
        ...options.headers,
    };
    // console.log('Request Headers:', headers);
    const token = getToken();
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }
    // console.log('Authorization:', headers.Authorization);
    const opts = {
        method: options.method || "GET",
        headers,
    };

    if (options.body) {
        opts.body = JSON.stringify(options.body);
    }

    try {
        console.log("apiClient URL", finalUrl, opts);
        const res = await fetch(finalUrl, opts);

        // Non-2xx handling 
        if (!res.ok) {
            const errText = await res.text();
            throw new Error(`API error ${res.status}: ${errText}`);
        }
        if (res.status === 401) {
            localStorage.removeItem("token");
            window.location.href = "/login";
        }

        // Handle no-content responses safely
        const text = await res.text();
        // console.log('API Response Text:', text);

        return text ? JSON.parse(text) : {};
    } catch (err) {
        console.error("API Error:", err);
        throw err;
    }
}

export default {
    get: (endpoint, params = {}, options = {}) =>
        request(
            endpoint +
            (Object.keys(params).length
                ? "?" + new URLSearchParams(params)
                : ""),
            { method: "GET", ...options }
        ),

    post: (endpoint, data = {}, options = {}) =>
        request(endpoint, { method: "POST", body: data, ...options }),

    put: (endpoint, data = {}, options = {}) =>
        request(endpoint, { method: "PUT", body: data, ...options }),

    del: (endpoint, options = {}) =>
        request(endpoint, { method: "DELETE", ...options }),
};
