import { getToken } from './auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const AUTH_URL = process.env.NEXT_PUBLIC_AUTH_URL || 'http://localhost:8000';
const CHAT_URL = process.env.NEXT_PUBLIC_CHAT_URL || 'http://localhost:5004';

async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, { ...options, headers });

  let data;
  try {
    data = await res.json();
  } catch {
    if (!res.ok) {
      throw new Error(`Request failed with status ${res.status}`);
    }
    return null;
  }

  if (!res.ok) {
    throw new Error(data.error || 'Request failed');
  }

  return data;
}

// Auth
export async function register(username: string, email: string, password: string) {
  return fetchWithAuth(`${AUTH_URL}/api/auth/register`, {
    method: 'POST',
    body: JSON.stringify({ username, email, password }),
  });
}

export async function login(email: string, password: string) {
  return fetchWithAuth(`${AUTH_URL}/api/auth/login`, {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function getMe() {
  return fetchWithAuth(`${AUTH_URL}/api/auth/me`);
}

// Rooms
export async function getRooms() {
  return fetchWithAuth(`${API_URL}/api/rooms/`);
}

export async function createRoom(name: string, description: string, topic: string) {
  return fetchWithAuth(`${API_URL}/api/rooms/`, {
    method: 'POST',
    body: JSON.stringify({ name, description, topic }),
  });
}

export async function getRoom(id: string) {
  return fetchWithAuth(`${API_URL}/api/rooms/${id}/`);
}

export async function joinRoom(id: string, code?: string) {
  return fetchWithAuth(`${API_URL}/api/rooms/${id}/join/`, {
    method: 'POST',
    body: JSON.stringify({ code }),
  });
}

export async function joinRoomByCode(code: string) {
  return fetchWithAuth(`${API_URL}/api/rooms/join-by-code/`, {
    method: 'POST',
    body: JSON.stringify({ code }),
  });
}

export async function leaveRoom(id: string) {
  return fetchWithAuth(`${API_URL}/api/rooms/${id}/leave/`, { method: 'POST' });
}

export async function deleteRoom(id: string) {
  return fetchWithAuth(`${API_URL}/api/rooms/${id}/`, { method: 'DELETE' });
}

// Messages — served by chat-service
export async function getMessages(roomId: string) {
  return fetchWithAuth(`${CHAT_URL}/api/chat/${roomId}/messages`);
}
