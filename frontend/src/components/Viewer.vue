<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { decryptFile, fragmentToRawKey, fromBase64 } from '../crypto';

const props = defineProps<{ fileId: string }>();

type Phase = 'loading' | 'confirm' | 'downloading' | 'decrypted' | 'error';
const phase = ref<Phase>('loading');
const errorTitle = ref<string>('');
const errorDetail = ref<string>('');
const meta = ref<{
  filename: string;
  size_bytes: number;
  expires_at: number;
  downloads_remaining: number;
} | null>(null);
const decryptedBlob = ref<Blob | null>(null);
const decryptedName = ref<string>('');
const remaining = ref<number>(0);

function fail(title: string, detail: string) {
  errorTitle.value = title;
  errorDetail.value = detail;
  phase.value = 'error';
}

function getKey(): Uint8Array | null {
  const frag = location.hash.replace(/^#/, '');
  const params = new URLSearchParams(frag);
  const k = params.get('k');
  return k ? fragmentToRawKey(k) : null;
}

onMounted(async () => {
  const key = getKey();
  if (!key) return fail('Invalid link', 'The URL is missing the decryption key fragment.');

  let res: Response;
  try {
    res = await fetch(`/api/files/${encodeURIComponent(props.fileId)}/meta`);
  } catch (err) {
    return fail('Network error', err instanceof Error ? err.message : String(err));
  }
  if (!res.ok) {
    return fail(
      'File unavailable',
      'This file has already been downloaded, expired, or never existed. By design, we cannot recover it.',
    );
  }
  meta.value = await res.json();
  phase.value = 'confirm';
});

async function reveal() {
  const key = getKey();
  if (!key) return fail('Invalid link', 'The URL is missing the decryption key fragment.');

  phase.value = 'downloading';
  let res: Response;
  try {
    res = await fetch(`/api/files/${encodeURIComponent(props.fileId)}`);
  } catch (err) {
    return fail('Network error', err instanceof Error ? err.message : String(err));
  }
  if (!res.ok) {
    return fail(
      'File unavailable',
      'Already downloaded or expired. By design, we cannot recover it.',
    );
  }
  const ivHeader = res.headers.get('X-VanishDrop-IV') || '';
  const filenameHeader = res.headers.get('X-VanishDrop-Filename') || 'download';
  const remainingHeader = res.headers.get('X-VanishDrop-Remaining') || '0';
  const ct = await res.arrayBuffer();
  let iv: Uint8Array;
  try {
    iv = fromBase64(ivHeader);
  } catch {
    return fail('Decryption failed', 'Bad IV from server.');
  }
  if (iv.length !== 12) return fail('Decryption failed', 'IV is the wrong length.');

  const opened = await decryptFile(ct, iv, key);
  if (!opened) {
    return fail(
      'Could not decrypt',
      "Wrong key in the URL, or the file was tampered with. Make sure you copied the entire URL including the part after the '#'.",
    );
  }
  decryptedBlob.value = new Blob([opened], { type: 'application/octet-stream' });
  decryptedName.value = filenameHeader;
  remaining.value = Number(remainingHeader);
  phase.value = 'decrypted';
}

function save() {
  if (!decryptedBlob.value) return;
  const url = URL.createObjectURL(decryptedBlob.value);
  const a = document.createElement('a');
  a.href = url;
  a.download = decryptedName.value;
  document.body.appendChild(a);
  a.click();
  a.remove();
  // Revoke after a tick so Safari has time to start the download.
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function humanSize(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KiB`;
  return `${(n / 1024 / 1024).toFixed(1)} MiB`;
}
</script>

<template>
  <section class="card" v-if="phase === 'loading'">
    <h2>Loading…</h2>
    <p class="muted">Checking that the file is still available.</p>
  </section>

  <section class="card" v-else-if="phase === 'confirm' && meta">
    <h2>One-time encrypted file</h2>
    <p class="muted">
      Downloading consumes one of <strong>{{ meta.downloads_remaining }}</strong> remaining
      downloads. The server copy is destroyed when the last download runs.
    </p>
    <p class="muted small">
      <strong>{{ meta.filename }}</strong> · {{ humanSize(meta.size_bytes) }} · expires
      {{ new Date(meta.expires_at * 1000).toLocaleString() }}
    </p>
    <button class="primary" @click="reveal">Decrypt &amp; download</button>
  </section>

  <section class="card" v-else-if="phase === 'downloading'">
    <h2>Downloading &amp; decrypting…</h2>
    <p class="muted">
      Streaming ciphertext from the server and decrypting locally with the URL-fragment key.
    </p>
  </section>

  <section class="card" v-else-if="phase === 'decrypted'">
    <h2>File ready</h2>
    <p class="muted">
      <strong>{{ decryptedName }}</strong> decrypted locally. Server copy is gone
      <template v-if="remaining > 0"> (still {{ remaining }} download(s) available)</template>.
    </p>
    <button class="primary" @click="save">Save to disk</button>
    <a href="/" class="ghost as-button">Send your own</a>
  </section>

  <section class="card error-card" v-else>
    <h2>{{ errorTitle }}</h2>
    <p class="muted">{{ errorDetail }}</p>
    <a href="/" class="ghost as-button">Send your own</a>
  </section>
</template>
