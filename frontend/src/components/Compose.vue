<script setup lang="ts">
import { ref, computed } from 'vue';
import { encryptFile, rawKeyToFragment } from '../crypto';

const file = ref<File | null>(null);
const ttl = ref<number>(86400);
const maxDownloads = ref<number>(1);

const status = ref<'idle' | 'encrypting' | 'uploading' | 'done' | 'error'>('idle');
const errorMsg = ref<string>('');
const resultUrl = ref<string>('');
const resultMeta = ref<string>('');

const sizeLabel = computed(() => (file.value ? humanSize(file.value.size) : ''));

function onPick(e: Event) {
  const target = e.target as HTMLInputElement;
  file.value = target.files && target.files[0] ? target.files[0] : null;
  errorMsg.value = '';
}

function onDrop(e: DragEvent) {
  e.preventDefault();
  const f = e.dataTransfer?.files?.[0];
  if (f) file.value = f;
}

async function submit() {
  if (!file.value) {
    errorMsg.value = 'Pick a file first.';
    return;
  }
  if (file.value.size > 32 * 1024 * 1024) {
    errorMsg.value = 'File too large (max 32 MiB).';
    return;
  }
  status.value = 'encrypting';
  errorMsg.value = '';

  const plaintext = await file.value.arrayBuffer();
  const { ciphertext, iv, key } = await encryptFile(plaintext);

  status.value = 'uploading';
  const form = new FormData();
  form.append('blob', new Blob([ciphertext], { type: 'application/octet-stream' }), 'blob');
  form.append('iv', toBase64Std(iv));
  form.append('filename', file.value.name);
  form.append('ttl_seconds', String(ttl.value));
  form.append('max_downloads', String(maxDownloads.value));

  let res: Response;
  try {
    res = await fetch('/api/files', { method: 'POST', body: form });
  } catch (err) {
    status.value = 'error';
    errorMsg.value = 'Network error: ' + (err instanceof Error ? err.message : String(err));
    return;
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    status.value = 'error';
    errorMsg.value = 'Upload failed: ' + (body.detail || res.statusText);
    return;
  }

  const body = await res.json();
  const fragment = rawKeyToFragment(key);
  resultUrl.value = `${location.origin}/d/${body.id}#k=${fragment}`;
  const expiry = new Date(body.expires_at * 1000);
  resultMeta.value = `Expires ${expiry.toLocaleString()} • burns after ${body.downloads_remaining} download${
    body.downloads_remaining === 1 ? '' : 's'
  } • ${humanSize(body.size_bytes)}`;
  status.value = 'done';
}

async function copy() {
  try {
    await navigator.clipboard.writeText(resultUrl.value);
  } catch (err) {
    console.warn('clipboard.writeText failed:', err);
  }
}

function reset() {
  file.value = null;
  resultUrl.value = '';
  resultMeta.value = '';
  status.value = 'idle';
}

function humanSize(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KiB`;
  return `${(n / 1024 / 1024).toFixed(1)} MiB`;
}

function toBase64Std(bytes: Uint8Array): string {
  let bin = '';
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}
</script>

<template>
  <section class="card" v-if="status !== 'done'">
    <h2>Drop a file to encrypt</h2>

    <label class="drop" @dragover.prevent @drop="onDrop">
      <input type="file" @change="onPick" class="file-input" />
      <div v-if="!file" class="drop-empty">
        <strong>Click to pick a file</strong>
        <span class="muted small">or drop one here · max 32 MiB</span>
      </div>
      <div v-else class="drop-filled">
        <strong>{{ file.name }}</strong>
        <span class="muted small">{{ sizeLabel }}</span>
      </div>
    </label>

    <div class="row">
      <div>
        <label for="ttl">Expires after</label>
        <select id="ttl" v-model.number="ttl">
          <option :value="3600">1 hour</option>
          <option :value="86400">24 hours</option>
          <option :value="604800">7 days</option>
        </select>
      </div>
      <div>
        <label for="dl">Max downloads</label>
        <select id="dl" v-model.number="maxDownloads">
          <option :value="1">1 (burn after download)</option>
          <option :value="3">3</option>
          <option :value="10">10</option>
        </select>
      </div>
    </div>

    <button
      class="primary"
      :disabled="!file || status === 'encrypting' || status === 'uploading'"
      @click="submit"
    >
      {{
        status === 'encrypting'
          ? 'Encrypting…'
          : status === 'uploading'
            ? 'Uploading ciphertext…'
            : 'Encrypt & upload'
      }}
    </button>

    <p v-if="errorMsg" class="err">{{ errorMsg }}</p>
  </section>

  <section class="card" v-else>
    <h2>Your one-time link</h2>
    <p class="muted">
      Send this URL to the recipient. <strong>Anyone with this URL can download the file once</strong> —
      treat it like the file itself.
    </p>
    <div class="link-row">
      <input type="text" :value="resultUrl" readonly />
      <button class="primary" @click="copy">Copy</button>
    </div>
    <p class="muted small">{{ resultMeta }}</p>
    <button class="ghost" @click="reset">Encrypt another</button>
  </section>
</template>
