<script setup>
const props = defineProps({
  motorId: { type: String, required: true },
  title: { type: String, required: true },
  currentValue: { type: Number, default: 0 },
  targetValue: { type: Number, default: 0 },
  modelValue: { type: Number, required: true },
  min: { type: Number, default: 0 },
  max: { type: Number, default: 100 },
  step: { type: Number, default: 1 },
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'commit', 'drag-start', 'drag-end'])

function onInput(event) {
  emit('update:modelValue', Number(event.target.value))
}

function onDragStart() {
  emit('drag-start', props.motorId)
}

function onDragEnd() {
  emit('drag-end', props.motorId)
}

function onCommit() {
  emit('commit', props.motorId)
}
</script>

<template>
  <section class="motor-card">
    <div class="header-row">
      <h3>{{ title }}</h3>
      <span class="target">Target {{ targetValue.toFixed(1) }}%</span>
    </div>

    <input
      class="motor-slider"
      type="range"
      :min="min"
      :max="max"
      :step="step"
      :disabled="disabled"
      :value="modelValue"
      @input="onInput"
      @pointerdown="onDragStart"
      @pointerup="onDragEnd"
      @change="onCommit"
    />

    <div class="values-row">
      <span>Setpoint {{ modelValue.toFixed(1) }}%</span>
      <span>Current {{ currentValue.toFixed(1) }}%</span>
    </div>
  </section>
</template>

<style scoped>
.motor-card {
  border-radius: 14px;
  border: 1px solid rgba(121, 147, 176, 0.35);
  background: linear-gradient(145deg, rgba(33, 49, 67, 0.94), rgba(17, 27, 40, 0.95));
  padding: 14px;
  display: grid;
  gap: 10px;
}

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
}

h3 {
  margin: 0;
  color: #d8ebff;
  font-size: 0.95rem;
  font-weight: 600;
}

.target {
  color: #78d2ff;
  font-size: 0.8rem;
}

.motor-slider {
  width: 100%;
  accent-color: #5ed2ff;
}

.values-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: #9fb8cf;
}
</style>
