const APP_SECRET_KEY = "ebay-monitor-app-secret";

export function getStoredAppSecret() {
  return window.localStorage.getItem(APP_SECRET_KEY) ?? "";
}

export function setStoredAppSecret(secret: string) {
  window.localStorage.setItem(APP_SECRET_KEY, secret);
}

export function clearStoredAppSecret() {
  window.localStorage.removeItem(APP_SECRET_KEY);
}

export function hasStoredAppSecret() {
  return Boolean(getStoredAppSecret());
}
