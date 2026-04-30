<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const alarms = ref([])
const loading = ref(true)
const error = ref(null)
let pollTimer = null
const POLL_MS = 2000

async function fetchAlarms() {
  try {
    const response = await fetch('/api/alarms')
    if (!response.ok) throw new Error('Failed to fetch alarms')
    
    const data = await response.json()
    alarms.value = data.alarms || []
    error.value = null
  } catch (err) {
    console.error('Error fetching alarms:', err)
    error.value = err.message
  } finally {
    loading.value = false
  }
}

function getAlarmClass(alarmType) {
  return `alarm-row alarm-${alarmType.toLowerCase()}`
}

function formatTimestamp(timestamp) {
  return timestamp
}

onMounted(() => {
  fetchAlarms()
  pollTimer = setInterval(fetchAlarms, POLL_MS)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="alarm-history-view">
    <div class="alarm-container">
      <h1>Alarm History</h1>

      <div v-if="error" class="error-banner">
        <span>Error: {{ error }}</span>
      </div>

      <div v-if="loading" class="loading-state">
        <p>Loading alarms...</p>
      </div>

      <div v-else-if="alarms.length === 0" class="empty-state">
        <p>No alarms or errors recorded yet.</p>
      </div>

      <div v-else class="alarms-list">
        <div class="list-header">
          <div class="col-timestamp">Timestamp</div>
          <div class="col-type">Type</div>
          <div class="col-message">Message</div>
        </div>

        <div v-for="(alarm, idx) in alarms" :key="`alarm-${idx}`" :class="getAlarmClass(alarm.type)">
          <div class="col-timestamp">{{ formatTimestamp(alarm.timestamp) }}</div>
          <div class="col-type">
            <span class="type-badge" :class="`badge-${alarm.type.toLowerCase()}`">
              {{ alarm.type.toUpperCase() }}
            </span>
          </div>
          <div class="col-message">{{ alarm.message }}</div>
        </div>
      </div>

      <div class="list-footer">
        <small>{{ alarms.length }} event(s) recorded</small>
      </div>
    </div>
  </div>
</template>

<style scoped>
.alarm-history-view {
  display: flex;
  justify-content: center;
  padding: 16px;
  min-height: calc(100vh - 100px);
}

.alarm-container {
  width: 100%;
  max-width: 1000px;
}

h1 {
  margin: 0 0 24px;
  font-size: 1.8rem;
  font-weight: 600;
  color: #dceeff;
}

.error-banner {
  background: rgba(255, 95, 109, 0.15);
  border: 1px solid rgba(255, 95, 109, 0.5);
  color: #ffb1b8;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 0.95rem;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #9bb4cd;
}

.empty-state {
  border-radius: 16px;
  border: 1px solid rgba(134, 176, 214, 0.25);
  background: linear-gradient(150deg, rgba(33, 49, 67, 0.92), rgba(17, 30, 45, 0.95));
}

.alarms-list {
  border-radius: 16px;
  border: 1px solid rgba(134, 176, 214, 0.25);
  background: linear-gradient(150deg, rgba(33, 49, 67, 0.92), rgba(17, 30, 45, 0.95));
  overflow: hidden;
}

.list-header {
  display: grid;
  grid-template-columns: 1fr 1fr 2fr;
  gap: 16px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(134, 176, 214, 0.15);
  font-weight: 600;
  font-size: 0.9rem;
  color: #a8c5e0;
}

.alarm-row {
  display: grid;
  grid-template-columns: 1fr 1fr 2fr;
  gap: 16px;
  padding: 16px;
  border-bottom: 1px solid rgba(134, 176, 214, 0.1);
  align-items: center;
}

.alarm-row:last-child {
  border-bottom: none;
}

.alarm-row.alarm-warning {
  background: rgba(255, 193, 7, 0.05);
}

.alarm-row.alarm-error {
  background: rgba(255, 87, 34, 0.08);
}

.col-timestamp {
  font-size: 0.85rem;
  color: #9bb4cd;
  font-family: 'Courier New', monospace;
}

.col-type {
  display: flex;
  justify-content: center;
}

.type-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.badge-warning {
  background: rgba(255, 193, 7, 0.2);
  color: #ffc107;
  border: 1px solid rgba(255, 193, 7, 0.4);
}

.badge-error {
  background: rgba(255, 87, 34, 0.2);
  color: #ff5722;
  border: 1px solid rgba(255, 87, 34, 0.4);
}

.col-message {
  color: #c0d9f0;
  font-size: 0.9rem;
}

.list-footer {
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(134, 176, 214, 0.1);
  text-align: right;
  color: #9bb4cd;
  font-size: 0.85rem;
}
</style>
