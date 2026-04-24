<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  motors: { type: Object, required: true }
})

const emit = defineEmits(['tau-changed'])

const tauValues = ref({})
const saving = ref(false)
const savedMessage = ref(null)
const editingMotorId = ref(null)

// Initialize tau values from props and update when they change
watch(
  () => props.motors?.motors,
  (newMotors) => {
    if (newMotors) {
      newMotors.forEach((motor) => {
        const motorKey = `motor_${motor.id}`
        const currentValue = tauValues.value[motorKey]
        
        // Ne pas réinitialiser si on est en train d'éditer ce moteur
        if (editingMotorId.value !== motor.id) {
          // Ne réinitialiser que si la valeur a changé sur le backend
          if (currentValue !== motor.tau_s) {
            tauValues.value[motorKey] = motor.tau_s
          }
        }
      })
    }
  },
  { immediate: true, deep: true }
)

async function saveTau(motorId, newTau) {
  saving.value = true
  try {
    const res = await fetch('/api/motor-tau', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        motor_id: motorId,
        tau_s: parseFloat(newTau)
      })
    })
    if (res.ok) {
      savedMessage.value = `Motor ${motorId} tau updated to ${newTau}s`
      editingMotorId.value = null
      emit('tau-changed', motorId, newTau)
      setTimeout(() => {
        savedMessage.value = null
      }, 3000)
    } else {
      savedMessage.value = 'Error saving tau'
    }
  } catch (error) {
    console.error('Error saving tau:', error)
    savedMessage.value = 'Error saving tau'
  }
  saving.value = false
}

function onTauInput(motorId, value) {
  editingMotorId.value = motorId
  tauValues.value[`motor_${motorId}`] = parseFloat(value) || 0
}

function onTauFocus(motorId) {
  editingMotorId.value = motorId
}

function onTauBlur() {
  editingMotorId.value = null
}
</script>

<template>
  <div class="settings-view">
    <div class="settings-container">
      <h2>Settings</h2>
      
      <div v-if="savedMessage" class="saved-message" :class="{ error: savedMessage.includes('Error') }">
        <span v-if="!savedMessage.includes('Error')" class="icon">✓</span>
        <span v-else class="icon error-icon">✗</span>
        {{ savedMessage }}
      </div>

      <section class="settings-section">
        <h3>Motor Configuration</h3>
        <p class="section-desc">Adjust the motor time constant (tau) which controls acceleration/deceleration speed.</p>

        <div v-if="motors.motors" class="motor-settings-grid">
          <article v-for="motor in motors.motors" :key="motor.id" class="motor-setting-card">
            <div class="motor-header">
              <h4>Motor {{ motor.id }}</h4>
              <span class="motor-id">ID: {{ motor.id }}</span>
            </div>

            <div class="setting-item">
              <label :for="`tau-input-${motor.id}`">Time Constant (τ) [seconds]</label>
              <div class="input-group">
                <input
                  :id="`tau-input-${motor.id}`"
                  type="number"
                  :value="tauValues[`motor_${motor.id}`] || motor.tau_s"
                  @input="onTauInput(motor.id, $event.target.value)"
                  @focus="onTauFocus(motor.id)"
                  @blur="onTauBlur"
                  :min="0.1"
                  :max="10"
                  :step="0.1"
                  :disabled="saving"
                  class="tau-input"
                />
                <span class="unit">s</span>
              </div>
              <small class="help-text">
                Lower values = faster response (0.1-10s recommended)
              </small>
            </div>

            <div class="current-value">
              <span>Current tau:</span>
              <span class="value">{{ motor.tau_s.toFixed(2) }}s</span>
            </div>

            <button
              class="save-button"
              @click="saveTau(motor.id, tauValues[`motor_${motor.id}`])"
              :disabled="saving || tauValues[`motor_${motor.id}`] === undefined || tauValues[`motor_${motor.id}`] === motor.tau_s"
            >
              {{ saving ? 'Saving...' : 'Save' }}
            </button>
          </article>
        </div>
      </section>

      <section class="settings-section info-section">
        <h3>About Time Constant</h3>
        <p>
          The time constant (τ) defines how quickly a motor reaches its target speed.
        </p>
        <ul>
          <li><strong>τ = 1.5s</strong> (faster): Motor reaches target in ~1.5 seconds</li>
          <li><strong>τ = 3.0s</strong> (slower): Motor reaches target in ~3 seconds</li>
          <li>Smaller values = snappier response, larger values = smoother transitions</li>
        </ul>
      </section>
    </div>
  </div>
</template>

<style scoped>
.settings-view {
  display: flex;
  justify-content: center;
  padding: 16px;
}

.settings-container {
  width: 100%;
  max-width: 800px;
}

h2 {
  margin: 0 0 24px;
  font-size: 1.8rem;
  font-weight: 600;
  color: #dceeff;
}

.saved-message {
  background: rgba(109, 255, 154, 0.15);
  border: 1px solid rgba(109, 255, 154, 0.5);
  color: #a1ff8f;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.saved-message.error {
  background: rgba(255, 95, 109, 0.15);
  border: 1px solid rgba(255, 95, 109, 0.5);
  color: #ffb1b8;
}

.saved-message .icon {
  font-weight: 700;
  font-size: 1.1rem;
}

.saved-message .error-icon {
  color: #ff5f6d;
}

.settings-section {
  border-radius: 16px;
  border: 1px solid rgba(134, 176, 214, 0.25);
  background: linear-gradient(150deg, rgba(33, 49, 67, 0.92), rgba(17, 30, 45, 0.95));
  padding: 20px;
  margin-bottom: 16px;
}

.settings-section h3 {
  margin: 0 0 8px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #d8ebff;
}

.section-desc {
  margin: 0 0 16px;
  color: #9bb4cd;
  font-size: 0.95rem;
}

.motor-settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.motor-setting-card {
  border-radius: 12px;
  border: 1px solid rgba(121, 147, 176, 0.35);
  background: linear-gradient(145deg, rgba(33, 49, 67, 0.94), rgba(17, 27, 40, 0.95));
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.motor-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
}

.motor-header h4 {
  margin: 0;
  font-size: 1.05rem;
  font-weight: 600;
  color: #d8ebff;
}

.motor-id {
  font-size: 0.8rem;
  color: #78d2ff;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.setting-item label {
  font-size: 0.9rem;
  font-weight: 500;
  color: #c0d9f0;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tau-input {
  flex: 1;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(121, 147, 176, 0.35);
  border-radius: 6px;
  color: #dceeff;
  font-size: 1rem;
  font-family: 'Rajdhani', sans-serif;
}

.tau-input:focus {
  outline: none;
  border-color: #58d0ff;
  box-shadow: 0 0 8px rgba(88, 208, 255, 0.3);
}

.tau-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.unit {
  color: #9bb4cd;
  font-size: 0.9rem;
  min-width: 20px;
}

.help-text {
  color: #7a8fa0;
  font-size: 0.8rem;
}

.current-value {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(88, 208, 255, 0.08);
  border-radius: 6px;
  font-size: 0.9rem;
  color: #9bb4cd;
}

.current-value .value {
  color: #58d0ff;
  font-weight: 600;
}

.save-button {
  padding: 10px 16px;
  background: linear-gradient(135deg, #58d0ff, #2bc5c1);
  border: none;
  border-radius: 6px;
  color: #0a1218;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.save-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(88, 208, 255, 0.4);
}

.save-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.info-section {
  background: linear-gradient(150deg, rgba(21, 60, 90, 0.6), rgba(15, 40, 60, 0.7));
}

.info-section ul {
  margin: 12px 0 0;
  padding-left: 20px;
  color: #9bb4cd;
}

.info-section li {
  margin-bottom: 8px;
  line-height: 1.5;
}
</style>
