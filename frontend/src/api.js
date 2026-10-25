import axios from "axios";

const API_BASE = "http://127.0.0.1:8000";

let authToken = localStorage.getItem("authToken") || null;

export function setAuthToken(token) {
  authToken = token;
  if (token) {
    localStorage.setItem("authToken", token);
  } else {
    localStorage.removeItem("authToken");
  }
}

export function logout() {
  setAuthToken(null);
}

export function getAuthToken() {
  return authToken;
}

const client = axios.create({ baseURL: API_BASE });

client.interceptors.request.use((config) => {
  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      setAuthToken(null);
      window.location.reload();
    }
    return Promise.reject(error);
  }
);

export async function login(email, password) {
  const res = await client.post("/auth/login", { email, password });
  return res.data.access_token;
}

export async function register(name, email, password) {
  const res = await client.post("/auth/register", { name, email, password });
  return res.data.access_token;
}

export async function sendChatMessage(message) {
  const res = await client.post("/chat", { message });
  return res.data;
}

export async function approveAction(approved) {
  const res = await client.post("/chat/approve", { approved });
  return res.data;
}

export async function getOrders() {
  const res = await client.get("/orders");
  return res.data;
}

export async function getTickets() {
  const res = await client.get("/tickets");
  return res.data;
}

export async function* streamChat(message, endpoint = "/chat/stream", body = { message }) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${authToken}`,
    },
    body: JSON.stringify(endpoint === "/chat/stream" ? { message } : body),
  });

  if (response.status === 401) {
    setAuthToken(null);
    window.location.reload();
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop();

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        yield JSON.parse(line.slice(6));
      }
    }
  }
}
export async function getChatHistory() {
  const res = await client.get("/chat/history");
  return res.data;
}