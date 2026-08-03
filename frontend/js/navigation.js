"use strict";

const CONSOLE_PATHS = new Set([
    "/index.html",
    "/data-center.html",
    "/iserver-tools.html",
    "/map3d.html",
    "/golden_standard.html",
]);

function resolveNextPath(rawValue, fallback = "/index.html") {
    if (!rawValue) return fallback;
    try {
        const target = new URL(String(rawValue), "http://tianyan.local");
        if (target.origin !== "http://tianyan.local" || !CONSOLE_PATHS.has(target.pathname)) {
            return fallback;
        }
        return `${target.pathname}${target.search}${target.hash}`;
    } catch {
        return fallback;
    }
}

function consoleLoginUrl(baseUrl, path) {
    const base = String(baseUrl || "").replace(/\/$/, "");
    return `${base}/login.html?next=${encodeURIComponent(resolveNextPath(path))}`;
}

if (typeof module !== "undefined" && module.exports) {
    module.exports = { CONSOLE_PATHS, resolveNextPath, consoleLoginUrl };
}
if (typeof window !== "undefined") {
    window.Navigation = { CONSOLE_PATHS, resolveNextPath, consoleLoginUrl };
}
