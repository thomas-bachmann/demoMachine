<script setup>
import { ref, onMounted } from 'vue'

const isOn = ref(false)
const hasWarning = ref(false)
const hasError = ref(false)
const loading = ref(false)
const backendAvailable = ref(true)

// Récupère l'état depuis le backend
async function fetchState() {
  try {
    const res = await fetch('/api/state')
    if (res.ok) {
      const data = await res.json()
      isOn.value = data.is_on
      hasWarning.value = data.has_warning
      hasError.value = data.has_error
      backendAvailable.value = true
    }
  } catch {
    backendAvailable.value = false
  }
}

async function toggleOnOff() {
  loading.value = true
  try {
    const res = await fetch('/api/toggle', { method: 'POST' })
    if (res.ok) {
      const data = await res.json()
      isOn.value = data.is_on
      hasWarning.value = data.has_warning
      hasError.value = data.has_error
    }
  } catch {
    backendAvailable.value = false
  }
  loading.value = false
}

async function simulateWarning() {
  if (!isOn.value) return
  loading.value = true
  try {
    const res = await fetch('/api/warning', { method: 'POST' })
    if (res.ok) {
      const data = await res.json()
      hasWarning.value = data.has_warning
    }
  } catch {
    backendAvailable.value = false
  }
  loading.value = false
}

async function simulateError() {
  if (!isOn.value) return
  loading.value = true
  try {
    const res = await fetch('/api/error', { method: 'POST' })
    if (res.ok) {
      const data = await res.json()
      hasError.value = data.has_error
    }
  } catch {
    backendAvailable.value = false
  }
  loading.value = false
}

onMounted(() => {
  fetchState()
})
</script>

<template>
  <div class="container">
    <h1>Demo Machine</h1>

    <div v-if="!backendAvailable" class="error-banner">
      Backend non disponible
    </div>
    
    <div class="leds">
      <div class="led-group">
        <div class="led" :class="{ on: isOn }"></div>
        <span>On</span>
      </div>
      <div class="led-group">
        <div class="led" :class="{ warning: hasWarning }"></div>
        <span>Warning</span>
      </div>
      <div class="led-group">
        <div class="led" :class="{ error: hasError }"></div>
        <span>Error</span>
      </div>
    </div>

    <div class="buttons">
      <button @click="toggleOnOff" :class="{ active: isOn }" :disabled="loading">
        {{ isOn ? 'Off' : 'On' }}
      </button>
      <button @click="simulateWarning" :disabled="!isOn || loading">
        Simulate Warning
      </button>
      <button @click="simulateError" :disabled="!isOn || loading">
        Simulate Error
      </button>
    </div>
  </div>
</template>

<style scoped>
.container {
  max-width: 400px;
  margin: 50px auto;
  text-align: center;
  font-family: Arial, sans-serif;
}

.error-banner {
  background-color: #ff4444;
  color: white;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.leds {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin: 40px 0;
}

.led-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.led {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background-color: #444;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.3);
  transition: all 0.3s ease;
}

.led.on {
  background-color: #00ff00;
  box-shadow: 0 0 15px #00ff00, inset 0 2px 4px rgba(255,255,255,0.3);
}

.led.warning {
  background-color: #ffaa00;
  box-shadow: 0 0 15px #ffaa00, inset 0 2px 4px rgba(255,255,255,0.3);
}

.led.error {
  background-color: #ff0000;
  box-shadow: 0 0 15px #ff0000, inset 0 2px 4px rgba(255,255,255,0.3);
}

.buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

button {
  padding: 12px 24px;
  font-size: 16px;
  border: none;
  border-radius: 6px;
  background-color: #2196F3;
  color: white;
  cursor: pointer;
  transition: background-color 0.2s;
}

button:hover:not(:disabled) {
  background-color: #1976D2;
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

button.active {
  background-color: #4CAF50;
}
</style>
