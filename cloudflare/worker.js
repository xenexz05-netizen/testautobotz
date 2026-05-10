/**
 * File2Link Bot — Cloudflare Worker Proxy
 * Deploy at: Cloudflare Dashboard → Workers → Create Worker
 * Update ORIGIN and BOT_DOMAIN before deploying.
 */

const ORIGIN = "https://YOUR-REPLIT-PROJECT.replit.app";
const BOT_DOMAIN = "yourdomain.com";

const CACHE_TTL = {
    streamPage: 300,
    mediaFile: 86400,
    rangePart: 3600,
    staticAsset: 604800,
    noCache: 0,
};

const NO_CACHE_ROUTES = ["/status", "/cdn-check", "/api/pushinfo"];
const STREAM_PAGE_PATTERN = /^\/watch\//;

addEventListener("fetch", event => {
    event.respondWith(handleRequest(event.request, event));
});

async function handleRequest(request, event) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (request.method === "OPTIONS") {
        return new Response(null, {
            status: 204,
            headers: {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
                "Access-Control-Allow-Headers": "Range, Content-Type, *",
                "Access-Control-Max-Age": "86400",
            },
        });
    }

    const originUrl = ORIGIN + path + url.search;
    const originRequest = new Request(originUrl, {
        method: request.method,
        headers: buildOriginHeaders(request),
        body: request.body,
        redirect: "follow",
    });

    const cacheConfig = getCacheConfig(path, request);

    if (cacheConfig.shouldCache && request.method === "GET") {
        const cache = caches.default;
        const cacheKey = new Request(originUrl, { headers: { Range: request.headers.get("Range") || "" } });
        const cached = await cache.match(cacheKey);
        if (cached) {
            const response = new Response(cached.body, cached);
            response.headers.set("X-Cache-Status", "HIT");
            return addSecurityHeaders(response);
        }
    }

    let originResponse;
    try {
        originResponse = await fetch(originRequest);
    } catch (err) {
        return new Response("Origin unavailable. Please try again shortly.", {
            status: 502,
            headers: { "Content-Type": "text/plain" },
        });
    }

    const response = new Response(originResponse.body, {
        status: originResponse.status,
        statusText: originResponse.statusText,
        headers: buildResponseHeaders(originResponse, cacheConfig),
    });

    if (cacheConfig.shouldCache && request.method === "GET" &&
        (originResponse.status === 200 || originResponse.status === 206)) {
        const cache = caches.default;
        const cacheKey = new Request(originUrl, { headers: { Range: request.headers.get("Range") || "" } });
        const cloneForCache = response.clone();
        (async () => {
            try { await cache.put(cacheKey, cloneForCache); } catch(e) {}
        })();
    }

    return addSecurityHeaders(response);
}

function buildOriginHeaders(request) {
    const headers = new Headers(request.headers);
    headers.set("X-Forwarded-For", request.headers.get("CF-Connecting-IP") || "unknown");
    headers.set("X-Real-IP", request.headers.get("CF-Connecting-IP") || "unknown");
    headers.set("X-Forwarded-Proto", "https");
    headers.set("X-Worker-Proxy", "true");
    const range = request.headers.get("Range");
    if (range) headers.set("Range", range);
    headers.delete("CF-Worker");
    return headers;
}

function buildResponseHeaders(originResponse, cacheConfig) {
    const headers = new Headers(originResponse.headers);
    if (cacheConfig.shouldCache) {
        headers.set("Cache-Control", `public, max-age=${cacheConfig.ttl}, stale-while-revalidate=60`);
        headers.set("CDN-Cache-Control", `max-age=${cacheConfig.ttl}`);
    } else {
        headers.set("Cache-Control", "no-store, no-cache, must-revalidate");
        headers.set("Pragma", "no-cache");
    }
    headers.set("Access-Control-Allow-Origin", "*");
    headers.set("Access-Control-Expose-Headers",
        "Content-Length, Content-Range, Content-Disposition, ETag, Accept-Ranges");
    headers.set("X-Cache-Status", "MISS");
    headers.set("X-Served-By", "File2Link-CF-Worker");
    return headers;
}

function addSecurityHeaders(response) {
    const headers = new Headers(response.headers);
    headers.set("X-Content-Type-Options", "nosniff");
    headers.set("X-Frame-Options", "SAMEORIGIN");
    headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
    headers.set("Strict-Transport-Security", "max-age=31536000; includeSubDomains");
    return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
}

function getCacheConfig(path, request) {
    if (NO_CACHE_ROUTES.some(route => path.startsWith(route))) {
        return { shouldCache: false, ttl: 0 };
    }
    if (STREAM_PAGE_PATTERN.test(path)) {
        return { shouldCache: true, ttl: CACHE_TTL.streamPage };
    }
    const rangeHeader = request.headers.get("Range");
    if (rangeHeader) {
        return { shouldCache: true, ttl: CACHE_TTL.rangePart };
    }
    if (path.length > 1 && !path.includes(".")) {
        return { shouldCache: true, ttl: CACHE_TTL.mediaFile };
    }
    return { shouldCache: false, ttl: 0 };
}
