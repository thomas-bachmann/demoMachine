<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import MotorSlider from './components/MotorSlider.vue'
import MotorSummaryCard from './components/MotorSummaryCard.vue'

const isOn = ref(false)
const hasWarning = ref(false)
const hasError = ref(false)
const loading = ref(false)
const backendAvailable = ref(true)
const emergencyStopActive = ref(false)
const emergencyStopAcknowledged = ref(false)
const motors = ref({
  motor_1: null,
  motor_2: null
})
const sliderValues = ref({
  motor_1: 0,
  motor_2: 0
})
const isDragging = ref({
  motor_1: false,
  motor_2: false
})
const speedHistory = ref({
  motor_1: [],
  motor_2: []
})

function getDefaultN8nUrl() {
  const { protocol, hostname } = window.location
  if (hostname.startsWith('app.')) {
    return `${protocol}//${hostname.replace(/^app\./, 'n8n.')}/n8n/`
  }
  return `${protocol}//${hostname}/n8n/`
}

const n8nUrl = import.meta.env.VITE_N8N_URL || getDefaultN8nUrl()

const HISTORY_WINDOW_MS = 10 * 60 * 1000

const motorCards = computed(() => {
  return [
    { id: 'motor_1', title: 'Motor 1', motor: motors.value.motor_1 },
    { id: 'motor_2', title: 'Motor 2', motor: motors.value.motor_2 }
  ]
})

function onSliderInput(motorId, value) {
  if (!motorId) return
  sliderValues.value[motorId] = Number(value)
}

function onDragStart(motorId) {
  if (!motorId) return
  isDragging.value[motorId] = true
}

function onDragEnd(motorId) {
  if (!motorId) return
  isDragging.value[motorId] = false
}

function openN8n() {
  window.open(n8nUrl, '_blank', 'noopener,noreferrer')
}

function updateSpeedHistory(motorId, speed) {
  const now = Date.now()
  speedHistory.value[motorId].push({ time: now, speed: Number(speed) || 0 })
  const cutoff = now - HISTORY_WINDOW_MS
  const trimmed = speedHistory.value[motorId].filter((entry) => entry.time >= cutoff)
  speedHistory.value[motorId] = trimmed.map((entry) => ({
    ...entry,
    x: ((entry.time - cutoff) / HISTORY_WINDOW_MS) * 100
  }))
}

// Fetches state from the backend
async function fetchState() {
  try {
    const res = await fetch('/api/state')
    if (res.ok) {
      const data = await res.json()
      isOn.value = data.is_on
      hasWarning.value = data.has_warning
      hasError.value = data.has_error
      emergencyStopActive.value = data.emergency_stop_active
      emergencyStopAcknowledged.value = data.emergency_stop_acknowledged
      backendAvailable.value = true
      motors.value.motor_1 = data.motor_1 || data.motor_slide || {}
      motors.value.motor_2 = data.motor_2 || {}
      updateSpeedHistory('motor_1', motors.value.motor_1?.current_speed ?? 0)
      updateSpeedHistory('motor_2', motors.value.motor_2?.current_speed ?? 0)
      if (!isDragging.value.motor_1) {
        sliderValues.value.motor_1 = motors.value.motor_1?.target_speed ?? 0
      }
      if (!isDragging.value.motor_2) {
        sliderValues.value.motor_2 = motors.value.motor_2?.target_speed ?? 0
      }
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

async function triggerEmergencyStop() {
  loading.value = true
  try {
    const res = await fetch('/api/emergency-stop', { method: 'POST' })
    if (res.ok) {
      const data = await res.json()
      emergencyStopActive.value = data.emergency_stop_active
      emergencyStopAcknowledged.value = data.emergency_stop_acknowledged
      isOn.value = data.is_on
    }
  } catch {
    backendAvailable.value = false
  }
  loading.value = false
}

async function acknowledgeEmergencyStop() {
  loading.value = true
  try {
    const res = await fetch('/api/emergency-stop-acknowledge', { method: 'POST' })
    if (res.ok) {
      const data = await res.json()
      emergencyStopAcknowledged.value = data.emergency_stop_acknowledged
    }
  } catch {
    backendAvailable.value = false
  }
  loading.value = false
}

async function commitSpeedTarget(motorId) {
  if (!motorId) return
  const motorIdNum = parseInt(motorId.split('_')[1])  // "motor_1" -> 1
  await fetch('/api/speed-target', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      target_speed: Number(sliderValues.value[motorId]),
      motor_id: motorIdNum
    })
  })
}

let pollTimer = null
const POLL_MS = 500

onMounted(() => {
  fetchState()
  pollTimer = setInterval(fetchState, POLL_MS)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="app-shell">
    <aside class="left-nav">
      <div class="brand">
        <span class="logo-dot"></span>
        <span class="brand-name">DemoMachine</span>
      </div>
      <nav>
        <button class="menu-item active" type="button">
          Monitoring
        </button>
        <button class="menu-item" type="button" @click="openN8n">
          n8n
        </button>
      </nav>
    </aside>

    <main class="dashboard">
      <header class="dashboard-header">
        <div>
          <h1>Production</h1>
          <p>Operator Interface - Real-time Machine Status</p>
        </div>
        <span class="clock-badge">Live</span>
      </header>

      <div v-if="!backendAvailable" class="error-banner">
        Backend Unavailable
      </div>

      <section class="kpi-grid">
        <article class="card">
          <h2>Machine</h2>
          <div class="status-row">
            <div class="led-group">
              <div class="led" :class="{ on: isOn }"></div>
              <span>Power</span>
            </div>
            <div class="led-group">
              <div class="led" :class="{ warning: hasWarning }"></div>
              <span>Warning</span>
            </div>
            <div class="led-group">
              <div class="led" :class="{ error: hasError }"></div>
              <span>Error</span>
            </div>
            <div class="led-group">
              <div class="led" :class="{ emergency: emergencyStopActive }"></div>
              <span>E-Stop</span>
            </div>
          </div>
        </article>
      </section>

      <section class="motors-grid" v-if="motors.motor_1 || motors.motor_2">
        <MotorSummaryCard
          v-for="motorCard in motorCards"
          :key="motorCard.id"
          :title="motorCard.title"
          :motor="motorCard.motor"
          :history="speedHistory[motorCard.id]"
        />
      </section>
    </main>

    <aside class="right-rail">
      <div class="rail-title">Machine control</div>
      <div class="buttons">
        <button @click="toggleOnOff" :class="{ active: isOn }" :disabled="loading || emergencyStopActive || hasError">
          {{ isOn ? 'Power Off' : 'Power On' }}
        </button>
        <button @click="simulateWarning" :disabled="loading || emergencyStopActive">
          Simulate Warning
        </button>
        <button @click="simulateError" :disabled="loading || emergencyStopActive">
          Simulate Error
        </button>
      </div>

      <div v-if="emergencyStopActive" class="emergency-stop-panel">
        <div class="emergency-title">EMERGENCY STOP ACTIVE</div>
        <button 
          class="emergency-button emergency-acknowledge" 
          @click="acknowledgeEmergencyStop"
          :disabled="loading || emergencyStopAcknowledged"
        >
          {{ emergencyStopAcknowledged ? 'Acknowledged ✓' : 'Acknowledge' }}
        </button>
      </div>

      <button 
        @click="triggerEmergencyStop" 
        class="emergency-button" 
        :disabled="loading"
      >
        ⚠ EMERGENCY STOP
      </button>

      <div class="slider-stack" v-if="motors.motor_1 || motors.motor_2">
        <MotorSlider
          v-for="motorCard in motorCards"
          :key="`slider-${motorCard.id}`"
          :motor-id="motorCard.id"
          :title="`${motorCard.title} Control`"
          :current-value="motorCard.motor?.current_speed ?? 0"
          :target-value="motorCard.motor?.target_speed ?? 0"
          :model-value="sliderValues[motorCard.id]"
          :disabled="!isOn || loading"
          @update:model-value="onSliderInput(motorCard.id, $event)"
          @drag-start="onDragStart"
          @drag-end="onDragEnd"
          @commit="commitSpeedTarget"
        />
      </div>
    </aside>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&display=swap');

.app-shell {
  --bg-1: #091522;
  --bg-2: #0e2134;
  --panel: #1a2a3b;
  --panel-strong: #24384d;
  --line: rgba(134, 176, 214, 0.25);
  --text-main: #dceeff;
  --text-muted: #9bb4cd;
  --accent: #58d0ff;
  --ok: #6dff9a;
  --warn: #ffbe4d;
  --err: #ff5f6d;
  min-height: 100vh;
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr) 320px;
  gap: 12px;
  padding: 12px;
  margin: 0px;
  background:
    radial-gradient(circle at 12% 8%, rgba(88, 208, 255, 0.14), transparent 28%),
    radial-gradient(circle at 84% 92%, rgba(61, 108, 255, 0.12), transparent 32%),
    linear-gradient(150deg, var(--bg-1), var(--bg-2));
  font-family: 'Rajdhani', sans-serif;
  color: var(--text-main);
}

.error-banner {
  background: rgba(255, 95, 109, 0.14);
  color: #ffb1b8;
  border: 1px solid rgba(255, 95, 109, 0.5);
  padding: 10px 12px;
  border-radius: 10px;
}

.left-nav,
.right-rail,
.card {
  border-radius: 16px;
  border: 1px solid var(--line);
  background: linear-gradient(150deg, rgba(33, 49, 67, 0.92), rgba(17, 30, 45, 0.95));
  box-shadow: 0 14px 32px rgba(4, 9, 17, 0.35);
}

.left-nav {
  padding: 16px;
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 16px;
  animation: slideInLeft 0.5s ease;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 18px var(--accent);
}

.brand-name {
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

nav {
  display: grid;
  align-content: start;
  gap: 8px;
}

.menu-item {
  text-align: left;
  background: rgba(13, 28, 44, 0.55);
  border: 1px solid transparent;
  color: var(--text-muted);
  padding: 11px 12px;
  border-radius: 10px;
  font-size: 0.95rem;
  transition: all 0.2s ease;
}

.menu-item:hover {
  color: var(--text-main);
  border-color: rgba(88, 208, 255, 0.4);
}

.dashboard {
  display: grid;
  align-content: start;
  gap: 12px;
  animation: fadeInUp 0.6s ease;
}

.dashboard-header {
  border-radius: 16px;
  border: 1px solid var(--line);
  background: linear-gradient(140deg, rgba(27, 44, 63, 0.92), rgba(19, 34, 52, 0.95));
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

h1 {
  margin: 0;
  font-size: 1.7rem;
}

p {
  margin: 6px 0 0;
  color: var(--text-muted);
}

.clock-badge {
  border-radius: 999px;
  border: 1px solid rgba(88, 208, 255, 0.45);
  background: rgba(88, 208, 255, 0.16);
  color: #a7e6ff;
  padding: 6px 14px;
}

.kpi-grid,
.motors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.card {
  padding: 14px;
}

.card h2 {
  margin: 0 0 12px;
  font-size: 1.04rem;
  font-weight: 600;
}

.status-row {
  display: flex;
  gap: 18px;
}

.led-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.led {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #2d3947;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.35);
}

.led.on {
  background: var(--ok);
  box-shadow: 0 0 14px rgba(109, 255, 154, 0.9);
}

.led.warning {
  background: var(--warn);
  box-shadow: 0 0 14px rgba(255, 190, 77, 0.9);
}

.led.error {
  background: var(--err);
  box-shadow: 0 0 14px rgba(255, 95, 109, 0.9);
}

.led.emergency {
  background: var(--err);
  box-shadow: 0 0 20px rgba(255, 95, 109, 1);
  animation: blink-emergency 0.5s infinite;
}

.metric-line {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  color: var(--text-muted);
}

.metric-line strong {
  color: var(--text-main);
}

.bar-track {
  height: 10px;
  border-radius: 999px;
  background: rgba(86, 121, 154, 0.3);
  overflow: hidden;
  margin: 8px 0;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #66d8ff, #58ffb8);
  transition: width 0.35s ease;
}

.right-rail {
  padding: 16px;
  display: grid;
  align-content: start;
  gap: 12px;
  animation: slideInRight 0.5s ease;
}

.rail-title {
  font-size: 1.1rem;
  font-weight: 700;
}

button {
  width: 100%;
  padding: 12px;
  font-size: 0.95rem;
  border: 1px solid rgba(118, 165, 205, 0.35);
  border-radius: 10px;
  background: linear-gradient(145deg, #264564, #17314b);
  color: var(--text-main);
  cursor: pointer;
  transition: all 0.2s ease;
}

button:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(88, 208, 255, 0.55);
}

button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

button.active {
  background: linear-gradient(145deg, #2f6e59, #1f5b47);
}

.buttons,
.slider-stack {
  display: grid;
  gap: 10px;
}

.emergency-stop-panel {
  background: rgba(255, 95, 109, 0.14);
  border: 2px solid var(--err);
  border-radius: 10px;
  padding: 12px;
  display: grid;
  gap: 10px;
  animation: pulse-emergency 1s infinite;
}

.emergency-title {
  font-weight: 700;
  color: var(--err);
  text-align: center;
  font-size: 0.9rem;
  letter-spacing: 0.05em;
}

.emergency-button {
  background: linear-gradient(145deg, #8b2626, #5a1818);
  border: 2px solid var(--err);
  color: #ffb1b8;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.emergency-button:hover:not(:disabled) {
  background: linear-gradient(145deg, #a73030, #7a2020);
  border-color: #ff9aa5;
  box-shadow: 0 0 12px rgba(255, 95, 109, 0.6);
}

.emergency-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.emergency-acknowledge {
  background: linear-gradient(145deg, #4a6b4a, #2a4a2a);
  border-color: var(--ok);
  color: #a7e6ff;
}

.emergency-acknowledge:hover:not(:disabled) {
  background: linear-gradient(145deg, #5a7b5a, #3a5a3a);
  border-color: #6dff9a;
  box-shadow: 0 0 12px rgba(109, 255, 154, 0.6);
}

@keyframes slideInLeft {
  from {
    transform: translateX(-14px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideInRight {
  from {
    transform: translateX(14px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes fadeInUp {
  from {
    transform: translateY(12px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

@keyframes blink-emergency {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

@keyframes pulse-emergency {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(255, 95, 109, 0.4);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(255, 95, 109, 0);
  }
}

@media (max-width: 1120px) {
  .app-shell {
    grid-template-columns: 180px 1fr;
  }

  .right-rail {
    grid-column: 1 / -1;
  }
}

@media (max-width: 760px) {
  .app-shell {
    grid-template-columns: 1fr;
  }

  .left-nav {
    grid-template-rows: auto;
  }

  nav {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
