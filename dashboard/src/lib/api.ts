const DEFAULT_API_BASE_URL = "http://localhost:8000";

function trimTrailingSlash(value: string) {
  return value.endsWith("/") ? value.slice(0, -1) : value;
}

export const API_BASE_URL = trimTrailingSlash(
  process.env.NEXT_PUBLIC_JARVIS_API_BASE_URL?.trim() || DEFAULT_API_BASE_URL
);

export const WS_BASE_URL = API_BASE_URL.replace(/^http/i, (protocol) =>
  protocol.toLowerCase() === "https" ? "wss" : "ws"
);

const AUTH_TOKEN = process.env.NEXT_PUBLIC_JARVIS_AUTH_TOKEN?.trim();

function buildHeaders(headersInit?: HeadersInit) {
  const headers = new Headers(headersInit);
  if (AUTH_TOKEN) {
    headers.set("x-auth-token", AUTH_TOKEN);
  }
  return headers;
}

async function readErrorMessage(response: Response) {
  try {
    const payload = (await response.json()) as { detail?: string };
    if (typeof payload.detail === "string" && payload.detail) {
      return payload.detail;
    }
  } catch {
    return `${response.status} ${response.statusText}`.trim();
  }

  return `${response.status} ${response.statusText}`.trim();
}

export async function apiFetch(path: string, init: RequestInit = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: buildHeaders(init.headers),
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response;
}
