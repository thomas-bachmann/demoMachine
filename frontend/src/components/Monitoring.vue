<script setup>
import { defineProps } from 'vue'
import MotorSummaryCard from './MotorSummaryCard.vue'

defineProps({
  isOn: { type: Boolean, required: true },
  hasWarning: { type: Boolean, required: true },
  doorOpen: { type: Boolean, required: true },
  errorActive: { type: Boolean, required: true },
  emergencyStopActive: { type: Boolean, required: true },
  motors: { type: Object, required: true },
  motorCards: { type: Array, required: true },
  speedHistory: { type: Object, required: true }
})
</script>

<template>
  <div class="monitoring-view">
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
            <div class="led" :class="{ error: errorActive }"></div>
            <span>Error</span>
          </div>
          <div class="led-group">
            <div class="led" :class="{ emergency: emergencyStopActive }"></div>
            <span>E-Stop</span>
          </div>
          <div class="led-group">
            <div class="led" :class="{ error: doorOpen }"></div>
            <span>Door</span>
          </div>
        </div>
      </article>
    </section>

    <section class="motors-grid" v-if="motors.motors?.[0] || motors.motors?.[1]">
      <MotorSummaryCard
        v-for="motorCard in motorCards"
        :key="motorCard.id"
        :title="motorCard.title"
        :motor="motorCard.motor"
        :history="speedHistory[motorCard.id]"
      />
    </section>
  </div>
</template>

<style scoped>
.monitoring-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 12px;
}

.motors-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 12px;
}

.card {
  border-radius: 16px;
  border: 1px solid rgba(134, 176, 214, 0.25);
  background: linear-gradient(150deg, rgba(33, 49, 67, 0.92), rgba(17, 30, 45, 0.95));
  padding: 16px;
}

.card h2 {
  margin: 0 0 12px;
  font-size: 1.1rem;
  font-weight: 600;
  color: #dceeff;
}

.status-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.led-group {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
  color: #9bb4cd;
}

.led {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #333;
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.5);
}

.led.on {
  background: #6dff9a;
  box-shadow: 0 0 8px #6dff9a;
}

.led.warning {
  background: #ffbe4d;
  box-shadow: 0 0 8px #ffbe4d;
}

.led.error {
  background: #ff5f6d;
  box-shadow: 0 0 8px #ff5f6d;
}

.led.emergency {
  background: #ff1744;
  box-shadow: 0 0 12px #ff1744;
}
</style>
