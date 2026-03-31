<template>
  <div class="refresh-frame" :class="{ 'is-refreshing': active }">
    <div v-if="active" class="refresh-overlay" aria-live="polite" role="status">
      <span class="refresh-status">同步中</span>
      <strong>{{ label }}</strong>
    </div>
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    active?: boolean;
    label?: string;
  }>(),
  {
    active: false,
    label: "正在更新",
  },
);
</script>

<style scoped>
.refresh-frame {
  position: relative;
  min-width: 0;
  transition: opacity 0.24s ease, transform 0.24s ease;
}

.refresh-frame.is-refreshing {
  transform: translateY(2px);
}

.refresh-overlay {
  position: absolute;
  top: -8px;
  right: 0;
  z-index: 3;
  display: inline-grid;
  gap: 2px;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 14px 30px rgba(15, 30, 39, 0.12);
  color: #24566a;
  min-width: 166px;
  backdrop-filter: blur(16px);
}

.refresh-overlay::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 12px;
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: linear-gradient(135deg, #2f7c98, #57b5e7);
  box-shadow: 0 0 0 0 rgba(87, 181, 231, 0.48);
  animation: pulse 1.2s ease-in-out infinite;
  transform: translateY(-50%);
}

.refresh-status {
  padding-left: 16px;
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #5d7b89;
}

.refresh-overlay strong {
  padding-left: 16px;
  font-size: 13px;
  line-height: 1.45;
  color: #173042;
}

.refresh-frame.is-refreshing::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 26px;
  pointer-events: none;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), transparent 32%);
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(87, 181, 231, 0.34);
  }
  50% {
    transform: scale(1.08);
    box-shadow: 0 0 0 8px rgba(87, 181, 231, 0);
  }
}

@media (max-width: 768px) {
  .refresh-overlay {
    left: 0;
    right: auto;
    top: -10px;
  }
}
</style>
