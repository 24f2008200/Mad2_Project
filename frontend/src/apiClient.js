// src/js/apiClient.js
import { getCommonParams } from '@/searchParams'
import { useRouter } from "vue-router";
const router = useRouter();

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:5000") + "/api";



// 2. Build URL with common + extra params (GET & DELETE)
function buildURLWithParams(endpoint, extraParams = {}) {
    const common = getCommonParams();
    const final = { ...common, ...extraParams };

    // Clean nulls
    const cleaned = Object.fromEntries(
        Object.entries(final).filter(([_, v]) => v !== null && v !== "")
    );

    const qs = new URLSearchParams(cleaned).toString();
    return qs ? `${API_BASE_URL}${endpoint}?${qs}` : `${API_BASE_URL}${endpoint}`;
}

// 3. Add common params to body (POST & PUT)
function mergeBodyWithCommon(data = {}) {
    const common = getCommonParams();
    const full = { ...data, ...common };

    // Clean nulls
    return Object.fromEntries(
        Object.entries(full).filter(([_, v]) => v !== null && v !== "")
    );
}

// 4. Token helper — avoids "Bearer null"
function authHeader() {
    const token = localStorage.getItem("access_token");
    return token ? { Authorization: `Bearer ${token}` } : {};
}

// 5. Request handler
async function request(url, options = {}) {
    const headers = {
        "Content-Type": "application/json",
        ...authHeader(),
        ...(options.headers || {}),
    };

    const fetchOptions = { ...options, headers };

    if (options.body) {
        fetchOptions.body = JSON.stringify(options.body);
    }
    try {
        console.log("apiClient URL", url, fetchOptions);
        const res = await fetch(url, fetchOptions);
        if (res.status >= 400) {
            console.log("API Response Error:", res.status);
            router.push("/login"); // redirect to login on error
            throw new Error(`API error: ${res.status}`);
        }
        const text = await res.text();
        return text ? JSON.parse(text) : {};
    }
    catch (err) {
        console.error("API Error:", err);
        throw err;
    }
}
export default {
    // GET: params → merged with common → URL query
    get(endpoint, params = {}, options = {}) {
        const url = buildURLWithParams(endpoint, params);
        return request(url, { method: "GET", ...options });
    },

    // DELETE: same as GET (URL params)
    del(endpoint, params = {}, options = {}) {
        const url = buildURLWithParams(endpoint, params);
        return request(url, { method: "DELETE", ...options });
    },

    // POST: common params merged INTO body
    post(endpoint, data = {}, options = {}) {
        const body = mergeBodyWithCommon(data);
        const url = `${API_BASE_URL}${endpoint}`;
        return request(url, { method: "POST", body, ...options });
    },

    // PUT: same as POST
    put(endpoint, data = {}, options = {}) {
        const body = mergeBodyWithCommon(data);
        const url = `${API_BASE_URL}${endpoint}`;
        return request(url, { method: "PUT", body, ...options });
    },
};
