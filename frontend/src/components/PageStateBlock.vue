<template>
  <div class="state-block" :class="[compact ? 'is-compact' : '', `is-${tone}`]" role="status" aria-live="polite">
    <span class="state-badge">{{ toneLabel }}</span>
    <strong>{{ title }}</strong>
    <p v-if="description">{{ description }}</p>
    <div v-if="$slots.default" class="state-extra">
      <slot />
    </div>
    <div v-if="actionLabel || $slots.actions" class="state-actions">
      <slot name="actions">
        <el-button plain @click="emit('action')">{{ actionLabel }}</el-button>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    title: string;
    description?: string;
    tone?: "loading" | "empty" | "error" | "info";
    compact?: boolean;
    actionLabel?: string;
  }>(),
  {
    description: "",
    tone: "info",
    compact: false,
    actionLabel: "",
  },
);

const emit = defineEmits<{
  (event: "action"): void;
}>();

const toneLabel = computed(() => {
  return {
    loading: "正在跟进",
    empty: "还没铺开",
    error: "需要处理",
    info: "给你个提示",
  }[props.tone];
});
</script>

<style scoped>
.state-block {
  display: grid;
  gap: 8px;
  padding: 14px 16px;
  border-radius: 18px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(247, 251, 255, 0.94)),
    radial-gradient(circle at top right, rgba(87, 181, 231, 0.1), transparent 30%);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
}

.state-block.is-compact {
  gap: 6px;
  padding: 12px 14px;
  border-radius: 16px;
}

.state-badge {
  justify-self: flex-start;
  padding: 5px 8px;
  border-radius: 999px;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #24566a;
  background: #e8f1f7;
}

.state-block:hover {
  transform: translateY(-2px);
  box-shadow: 0 24px 54px rgba(15, 30, 39, 0.12);
  border-color: rgba(16, 34, 42, 0.12);
}

.state-block strong {
  font-size: 16px;
  color: #173042;
  line-height: 1.35;
}

.state-block p {
  margin: 0;
  color: #476072;
  line-height: 1.55;
  font-size: 13px;
}

.state-extra,
.state-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.state-block.is-loading {
  background: rgba(246, 250, 253, 0.94);
}

.state-block.is-empty .state-badge {
  background: rgba(232, 241, 247, 0.95);
}

.state-block.is-error .state-badge {
  background: rgba(255, 233, 231, 0.9);
  color: #8a3e35;
}

.state-block.is-info .state-badge {
  background: rgba(230, 244, 236, 0.92);
  color: #1f6a4c;
}
</style>
