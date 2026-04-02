<template>
  <div class="compact-hint" :class="`tone-${tone}`">
    <button type="button" class="compact-hint-trigger" :aria-label="title || label">
      <span class="compact-hint-dot" aria-hidden="true" />
      <span>{{ label }}</span>
    </button>
    <div class="compact-hint-panel" role="note">
      <strong v-if="title">{{ title }}</strong>
      <p>{{ description }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    label?: string;
    title?: string;
    description: string;
    tone?: "default" | "warm" | "accent";
  }>(),
  {
    label: "说明",
    title: "",
    tone: "default",
  },
);
</script>

<style scoped>
.compact-hint {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.compact-hint-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  border-radius: 999px;
  background: rgba(247, 251, 255, 0.92);
  color: #476072;
  font-size: 12px;
  font-weight: 700;
}

.compact-hint-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: rgba(60, 125, 255, 0.88);
  box-shadow: 0 0 0 4px rgba(60, 125, 255, 0.1);
}

.tone-warm .compact-hint-dot {
  background: rgba(255, 138, 28, 0.92);
  box-shadow: 0 0 0 4px rgba(255, 138, 28, 0.1);
}

.tone-accent .compact-hint-dot {
  background: rgba(138, 91, 255, 0.92);
  box-shadow: 0 0 0 4px rgba(138, 91, 255, 0.1);
}

.compact-hint-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: 40;
  display: grid;
  gap: 6px;
  width: min(320px, calc(100vw - 32px));
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(15, 26, 34, 0.96);
  box-shadow: 0 18px 36px rgba(15, 30, 39, 0.18);
  opacity: 0;
  pointer-events: none;
  transform: translateY(6px);
  transition: opacity var(--app-ease), transform var(--app-ease);
}

.compact-hint:hover .compact-hint-panel,
.compact-hint:focus-within .compact-hint-panel {
  opacity: 1;
  pointer-events: auto;
  transform: translateY(0);
}

.compact-hint-panel strong {
  color: #f7fbff;
  font-size: 13px;
}

.compact-hint-panel p {
  margin: 0;
  color: rgba(239, 247, 251, 0.8);
  font-size: 12px;
  line-height: 1.55;
}

@media (max-width: 768px) {
  .compact-hint-panel {
    right: auto;
    left: 0;
  }
}
</style>
