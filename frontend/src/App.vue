<script setup lang="ts">
import { ref, onMounted } from 'vue';
import Compose from './components/Compose.vue';
import Viewer from './components/Viewer.vue';

// Routing without a router: a /d/<id> path means viewer; everything else means compose.
const route = ref<'compose' | 'view'>('compose');
const fileId = ref<string>('');

onMounted(() => {
  const m = location.pathname.match(/^\/d\/([A-Za-z0-9_-]+)\/?$/);
  if (m) {
    route.value = 'view';
    fileId.value = m[1];
  }
});
</script>

<template>
  <main class="shell">
    <header>
      <h1><span class="lock">🔐</span> VanishDrop</h1>
      <p class="tagline">
        Encrypted one-time file sharing. The server only sees ciphertext blobs; the AES-GCM key
        lives in the URL fragment and never reaches our servers.
      </p>
    </header>

    <Compose v-if="route === 'compose'" />
    <Viewer v-else :file-id="fileId" />

    <footer>
      <p class="muted small">
        Cipher: AES-GCM (256-bit key, 96-bit IV) via the Web Crypto API.
        <a href="https://github.com/repobility/vanishdrop">Source on GitHub</a>.
      </p>
    </footer>
  </main>
</template>
