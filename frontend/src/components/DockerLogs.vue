<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const containers = ref([])
const selectedContainer = ref(null)
const logs = ref('')
const loading = ref(false)
const error = ref(null)
const autoScroll = ref(true)

let pollTimer = null
const POLL_MS = 2000

async function fetchContainers() {
  try {
    const response = await fetch('/api/logs')
    if (!response.ok) throw new Error('Failed to fetch containers')
    
    const data = await response.json()
    if (data.containers) {
      containers.value = data.containers
      if (!selectedContainer.value && containers.value.length > 0) {
        selectedContainer.value = containers.value[0].name
      }
    }
    error.value = null
  } catch (err) {
    console.error('Error fetching containers:', err)
    error.value = err.message
  }
}

async function fetchLogs() {
  if (!selectedContainer.value) return
  
  loading.value = true
  try {
    const response = await fetch(`/api/logs?docker=${selectedContainer.value}`)
    if (!response.ok) throw new Error('Failed to fetch logs')
    
    const data = await response.json()
    if (data.logs) {
      logs.value = data.logs
    } else if (data.error) {
      error.value = data.error
      logs.value = ''
    }
    error.value = null
  } catch (err) {
    console.error('Error fetching logs:', err)
    error.value = err.message
  } finally {
    loading.value = false
    
    // Auto-scroll to bottom
    if (autoScroll.value) {
      setTimeout(() => {
        const logElement = document.querySelector('.docker-logs-content')
        if (logElement) {
          logElement.scrollTop = logElement.scrollHeight
        }
      }, 10)
    }
  }
}

function onContainerChange(newContainer) {
  selectedContainer.value = newContainer
  logs.value = ''
  fetchLogs()
}

function toggleAutoScroll() {
  autoScroll.value = !autoScroll.value
}

function copyLogs() {
  navigator.clipboard.writeText(logs.value).then(() => {
    // Could show a toast notification here
  })
}

onMounted(() => {
  fetchContainers()
  if (selectedContainer.value) {
    fetchLogs()
  }
  pollTimer = setInterval(() => {
    if (selectedContainer.value) {
      fetchLogs()
    }
  }, POLL_MS)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="docker-logs-view">
    <div class="docker-logs-container">
      <h1>Docker Logs</h1>

      <div v-if="error" class="error-banner">
        <span>Error: {{ error }}</span>
      </div>

      <div class="logs-header">
        <div class="container-selector">
          <label for="container-select">Select Container:</label>
          <select
            id="container-select"
            :value="selectedContainer"
            @change="onContainerChange($event.target.value)"
            :disabled="loading"
          >
            <option value="">-- Choose a container --</option>
            <option
              v-for="container in containers"
              :key="container.name"
              :value="container.name"
            >
              {{ container.name }} ({{ container.status }})
            </option>
          </select>
        </div>

        <div class="logs-controls">
          <button
            :class="{ active: autoScroll }"
            @click="toggleAutoScroll"
            :disabled="loading"
            title="Auto-scroll to bottom"
          >
            {{ autoScroll ? '📍 Auto-scroll' : '📍 Manual scroll' }}
          </button>
          <button
            @click="copyLogs"
            :disabled="loading || !logs"
            title="Copy logs to clipboard"
          >
            📋 Copy
          </button>
          <button
            @click="fetchLogs"
            :disabled="loading || !selectedContainer"
            title="Refresh logs"
          >
            {{ loading ? '⟳ Loading...' : '⟳ Refresh' }}
          </button>
        </div>
      </div>

      <div v-if="!selectedContainer" class="empty-state">
        <p>Select a container to view its logs</p>
      </div>

      <div v-else class="docker-logs-content">
        <pre>{{ logs || 'No logs available' }}</pre>
      </div>
    </div>
  </div>
</template>

<style scoped>
.docker-logs-view {
  display: flex;
  justify-content: center;
  padding: 16px;
  min-height: calc(100vh - 100px);
}

.docker-logs-container {
  width: 100%;
  max-width: 1200px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

h1 {
  margin: 0 0 16px;
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
  font-size: 0.95rem;
}

.logs-header {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.container-selector {
  flex: 1;
  min-width: 250px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.container-selector label {
  font-size: 0.9rem;
  font-weight: 600;
  color: #c0d9f0;
}

.container-selector select {
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(121, 147, 176, 0.35);
  border-radius: 6px;
  color: #dceeff;
  font-size: 0.95rem;
  font-family: 'Rajdhani', sans-serif;
}

.container-selector select:focus {
  outline: none;
  border-color: #58d0ff;
  box-shadow: 0 0 8px rgba(88, 208, 255, 0.3);
}

.container-selector select:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.logs-controls {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

button {
  padding: 8px 16px;
  background: rgba(88, 208, 255, 0.1);
  border: 1px solid rgba(88, 208, 255, 0.4);
  border-radius: 6px;
  color: #58d0ff;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

button:hover:not(:disabled) {
  background: rgba(88, 208, 255, 0.2);
  border-color: #58d0ff;
  box-shadow: 0 2px 8px rgba(88, 208, 255, 0.2);
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

button.active {
  background: rgba(88, 208, 255, 0.3);
  border-color: #58d0ff;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #9bb4cd;
  border-radius: 16px;
  border: 1px solid rgba(134, 176, 214, 0.25);
  background: linear-gradient(150deg, rgba(33, 49, 67, 0.92), rgba(17, 30, 45, 0.95));
}

.docker-logs-content {
  flex: 1;
  border-radius: 16px;
  border: 1px solid rgba(134, 176, 214, 0.25);
  background: rgba(0, 0, 0, 0.5);
  padding: 16px;
  overflow: auto;
  max-height: 600px;
  font-family: 'Monaco', 'Courier New', monospace;
}

.docker-logs-content pre {
  margin: 0;
  color: #58d0ff;
  font-size: 0.85rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

@media (max-width: 768px) {
  .logs-header {
    flex-direction: column;
    align-items: stretch;
  }

  .container-selector {
    min-width: unset;
  }

  .logs-controls {
    width: 100%;
    justify-content: stretch;
  }

  button {
    flex: 1;
  }
}
</style>
