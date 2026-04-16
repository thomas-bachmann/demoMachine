<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, required: true },
  motor: { type: Object, required: true },
  history: { type: Array, default: () => [] }
})

const speedPath = computed(() => {
  if (!props.history.length) return ''
  const width = 100
  const height = 32

  const points = props.history.map((entry) => {
    const clampedSpeed = Math.min(100, Math.max(0, Number(entry.speed) || 0))
    const x = Math.min(width, Math.max(0, Number(entry.x) || 0))
    const y = height - (clampedSpeed / 100) * height
    return {
      x,
      y: Math.min(height, Math.max(0, y))
    }
  })

  if (points.length === 1) {
    return `M 0 ${points[0].y.toFixed(2)} L ${width} ${points[0].y.toFixed(2)}`
  }

  return points
    .map((point, idx) => `${idx === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
    .join(' ')
})

const currentSpeed = computed(() => Number(props.motor?.current_speed) || 0)
const targetSpeed = computed(() => Number(props.motor?.target_speed) || 0)
const tauS = computed(() => Number(props.motor?.tau_s) || 0)
</script>

<template>
  <article class="card motor-summary-card">
    <h2>{{ title }}</h2>
    <p>Current: {{ currentSpeed.toFixed(1) }}%</p>
    <p>Target: {{ targetSpeed.toFixed(1) }}%</p>
    <p>Tau: {{ tauS.toFixed(2) }}s</p>

    <div class="speed-history-chart">
      <svg viewBox="0 0 100 32" preserveAspectRatio="none" :aria-label="`${title} speed over last ten minutes`">
        <line x1="0" y1="0" x2="100" y2="0" class="grid-line" />
        <line x1="0" y1="16" x2="100" y2="16" class="grid-line" />
        <line x1="0" y1="32" x2="100" y2="32" class="grid-line" />
        <path v-if="speedPath" :d="speedPath" class="speed-line" />
        <circle
          v-for="(entry, idx) in history"
          :key="`${title}-${idx}`"
          :cx="Math.min(100, Math.max(0, Number(entry.x) || 0))"
          :cy="32 - (Math.min(100, Math.max(0, Number(entry.speed) || 0)) / 100) * 32"
          class="speed-point"
          r="0.22"
        />
      </svg>
      <div v-if="!speedPath" class="chart-empty">Waiting for data...</div>
    </div>

    <div class="chart-footer">
      <span>-10 min</span>
      <span>{{ currentSpeed.toFixed(1) }}%</span>
      <span>now</span>
    </div>
    <small>{{ history.length }} points</small>
  </article>
</template>

<style scoped>
.motor-summary-card {
  display: grid;
  gap: 8px;
}

h2 {
  margin: 0 0 8px;
  font-size: 1.04rem;
  font-weight: 600;
}

p {
  margin: 4px 0;
}

.speed-history-chart {
  position: relative;
  height: 170px;
  border-radius: 12px;
  border: 1px solid rgba(134, 176, 214, 0.3);
  background: linear-gradient(160deg, rgba(14, 34, 52, 0.85), rgba(9, 24, 39, 0.92));
  overflow: hidden;
}

.speed-history-chart svg {
  width: 100%;
  height: 100%;
  display: block;
}

.grid-line {
  stroke: rgba(155, 180, 205, 0.28);
  stroke-width: 0.35;
}

.speed-line {
  fill: none;
  stroke: #58d0ff;
  stroke-width: 0.7;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.speed-point {
  fill: #7ddfff;
  opacity: 0.75;
}

.chart-empty {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: #9bb4cd;
  font-size: 0.9rem;
}

.chart-footer {
  display: flex;
  justify-content: space-between;
  color: #9bb4cd;
  font-size: 0.85rem;
}

small {
  color: #9bb4cd;
}
</style>