/**
 * VanishDrop crypto — Web Crypto API.
 *
 * Primitive: AES-GCM with a 256-bit key and 96-bit (12-byte) IV.
 * - Encrypt: browser generates a fresh key + IV, encrypts the file bytes,
 *   exports the key as raw 32 bytes.
 * - The exported key is what travels in the URL fragment (`#k=...`).
 *   Browsers never send fragments in HTTP, so the server never sees the key.
 * - Decrypt: viewer page reads the key from the URL fragment, the IV from
 *   the response header, and decrypts the response body.
 */

const KEY_BYTES = 32;
const IV_BYTES = 12;

export interface EncryptedFile {
  ciphertext: ArrayBuffer;
  iv: Uint8Array;
  key: Uint8Array; // raw 32 bytes — stays in the URL fragment, never on the wire
}

export async function encryptFile(plaintext: ArrayBuffer): Promise<EncryptedFile> {
  const key = crypto.getRandomValues(new Uint8Array(KEY_BYTES));
  const iv = crypto.getRandomValues(new Uint8Array(IV_BYTES));
  const cryptoKey = await crypto.subtle.importKey('raw', key, 'AES-GCM', false, ['encrypt']);
  const ciphertext = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, cryptoKey, plaintext);
  return { ciphertext, iv, key };
}

export async function decryptFile(
  ciphertext: ArrayBuffer,
  iv: Uint8Array,
  rawKey: Uint8Array,
): Promise<ArrayBuffer | null> {
  try {
    const cryptoKey = await crypto.subtle.importKey('raw', rawKey, 'AES-GCM', false, ['decrypt']);
    return await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, cryptoKey, ciphertext);
  } catch {
    return null;
  }
}

// ---------- base64 (standard) ----------

export function toBase64(bytes: Uint8Array): string {
  let bin = '';
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}

export function fromBase64(s: string): Uint8Array {
  const bin = atob(s);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

// ---------- urlsafe base64 (RFC 4648 §5, no padding) ----------

export function toUrlSafe(b64: string): string {
  return b64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

export function fromUrlSafe(b64u: string): string {
  const s = b64u.replace(/-/g, '+').replace(/_/g, '/');
  const pad = (4 - (s.length % 4)) % 4;
  return s + '='.repeat(pad);
}

export function rawKeyToFragment(key: Uint8Array): string {
  return toUrlSafe(toBase64(key));
}

export function fragmentToRawKey(fragment: string): Uint8Array | null {
  try {
    const bytes = fromBase64(fromUrlSafe(fragment));
    return bytes.length === KEY_BYTES ? bytes : null;
  } catch {
    return null;
  }
}
