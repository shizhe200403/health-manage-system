<template>
  <section class="page admin-operation-logs">
    <div class="head">
      <div>
        <p class="tag">Operation Logs</p>
        <h2>操作日志</h2>
        <p class="desc">把后台处理动作沉淀下来，回看是谁改了什么、为什么改、改完有没有把主线拉稳。</p>
      </div>
      <div class="head-actions">
        <el-button plain @click="resetFilters">重置筛选</el-button>
        <el-button type="primary" :loading="loading" @click="loadLogs">刷新日志</el-button>
        <el-button plain @click="router.push(resolveOpsHome(auth.user))">回后台首页</el-button>
      </div>
    </div>

    <PageStateBlock
      v-if="auth.isAuthenticated && !auth.user"
      tone="loading"
      title="正在确认后台身份"
      description="先把账号权限拉齐，再展开后台操作日志。"
      compact
    />
    <PageStateBlock
      v-else-if="!hasOpsUser"
      tone="error"
      title="当前账号没有后台权限"
      description="操作日志只对后台值守账号开放，普通账号不会显示这里。"
      action-label="回到首页"
      @action="router.push('/')"
    />
    <template v-else>
      <CollectionSkeleton v-if="loading && !logs.length" variant="dashboard" :card-count="4" />
      <RefreshFrame v-else :active="loading" label="正在同步后台操作日志">
        <div class="summary-grid">
          <article v-spotlight>
            <span>日志总量</span>
            <strong>{{ summary.total }}</strong>
            <p>当前筛选下累计沉淀的后台处理动作数量。</p>
          </article>
          <article v-spotlight>
            <span>今天新增</span>
            <strong>{{ summary.today_total }}</strong>
            <p>这能更直观看出后台今天到底有没有在真实处理内容。</p>
          </article>
          <article v-spotlight>
            <span>参与值守</span>
            <strong>{{ summary.unique_operators }}</strong>
            <p>不同管理员的操作轨迹越清楚，后面越容易复盘责任边界。</p>
          </article>
          <article v-spotlight>
            <span>社区处理</span>
            <strong>{{ summary.community_actions }}</strong>
            <p>帖子、举报和评论动作会集中沉淀在这里。</p>
          </article>
        </div>

        <div class="ops-alert-strip">
          <article v-for="item in moduleCards" :key="item.label" class="ops-alert-card" v-spotlight>
            <span>{{ item.label }}</span>
            <strong>{{ item.value }}</strong>
            <p>{{ item.copy }}</p>
          </article>
        </div>

        <article class="card console-card" v-spotlight>
          <div class="card-head">
            <div>
              <h3>筛选与检索</h3>
              <p>先按模块或操作人收窄，再看具体字段前后变化，复盘会比从全量列表硬翻快很多。</p>
            </div>
          </div>
          <div class="toolbar-grid">
            <el-select v-model="filters.module" clearable placeholder="筛选模块">
              <el-option label="用户管理" value="users" />
              <el-option label="菜谱管理" value="recipes" />
              <el-option label="社区审核" value="community" />
              <el-option label="运营复核" value="reports" />
            </el-select>
            <el-input v-model.trim="filters.actor" placeholder="搜索操作人" clearable @keyup.enter="loadLogs" />
            <el-input v-model.trim="filters.keyword" placeholder="搜索对象或动作摘要" clearable @keyup.enter="loadLogs" />
            <el-button type="primary" :loading="loading" @click="loadLogs">应用筛选</el-button>
          </div>
        </article>

        <article class="card console-card" v-spotlight>
          <div class="card-head">
            <div>
              <h3>最近处理动作</h3>
              <p>重点看本轮处理到底改了哪些字段，避免后台只有结果、没有过程。</p>
            </div>
            <span class="table-meta">当前显示 {{ logs.length }} / {{ total }} 条</span>
          </div>

          <div v-if="logs.length" class="log-list">
            <article v-for="log in logs" :key="log.id" class="log-item">
              <div class="log-head">
                <div>
                  <div class="log-topline">
                    <el-tag size="small" :type="moduleTagType(log.module)" effect="light">{{ moduleLabel(log.module) }}</el-tag>
                    <span>{{ formatDateTime(log.created_at) }}</span>
                  </div>
                  <strong>{{ log.summary }}</strong>
                  <p>{{ buildMetaLine(log) }}</p>
                </div>
                <div class="log-actor">
                  <span>操作人</span>
                  <strong>{{ log.actor?.display_name || log.actor?.username || "系统" }}</strong>
                </div>
              </div>

              <div v-if="log.changes?.length" class="change-list">
                <article v-for="(change, index) in log.changes" :key="`${log.id}-${index}-${change.field}`" class="change-item">
                  <div class="change-head">
                    <strong>{{ change.section ? `${change.section} · ${change.label}` : change.label }}</strong>
                    <span>{{ change.field }}</span>
                  </div>
                  <div class="change-values">
                    <div>
                      <span>修改前</span>
                      <strong>{{ formatChangeValue(change.before) }}</strong>
                    </div>
                    <div>
                      <span>修改后</span>
                      <strong>{{ formatChangeValue(change.after) }}</strong>
                    </div>
                  </div>
                </article>
              </div>
              <div v-else class="change-empty">这条动作没有记录字段差异，主要用来保留处理轨迹。</div>
            </article>
          </div>
          <PageStateBlock
            v-else
            tone="empty"
            title="当前筛选下还没有日志"
            description="可以放宽筛选条件，或先去后台各模块处理几条动作后再回来复盘。"
            compact
          />
        </article>
      </RefreshFrame>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import { listAdminOperationLogs } from "../api/adminLogs";
import { hasOpsAccess, resolveOpsHome } from "../lib/opsAccess";
import { notifyLoadError } from "../lib/feedback";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();

const loading = ref(false);
const logs = ref<any[]>([]);
const total = ref(0);
const summary = ref({
  total: 0,
  today_total: 0,
  unique_operators: 0,
  user_actions: 0,
  recipe_actions: 0,
  community_actions: 0,
  report_actions: 0,
});
const filters = reactive({
  module: "",
  actor: "",
  keyword: "",
});

const hasOpsUser = computed(() => hasOpsAccess(auth.user));
const moduleCards = computed(() => [
  {
    label: "用户侧动作",
    value: summary.value.user_actions,
    copy: summary.value.user_actions > 0 ? "账号状态、角色边界和资料改动已经开始沉淀可追踪记录。" : "当前筛选下还没有用户管理动作。",
  },
  {
    label: "菜谱侧动作",
    value: summary.value.recipe_actions,
    copy: summary.value.recipe_actions > 0 ? "菜谱审核、状态调整和归档动作都能回看了。" : "当前筛选下还没有菜谱处理动作。",
  },
  {
    label: "社区侧动作",
    value: summary.value.community_actions,
    copy: summary.value.community_actions > 0 ? "帖子审核、举报处理和评论隐藏已经能串成完整轨迹。" : "当前筛选下还没有社区处理动作。",
  },
]);

onMounted(() => {
  if (hasOpsUser.value) {
    void loadLogs();
  }
});

function unwrapItems(payload: any) {
  if (Array.isArray(payload?.data?.items)) return payload.data.items;
  if (Array.isArray(payload?.items)) return payload.items;
  return [];
}

async function loadLogs() {
  if (!hasOpsUser.value) return;
  loading.value = true;
  try {
    const response = await listAdminOperationLogs({
      page: 1,
      page_size: 20,
      module: filters.module || undefined,
      actor: filters.actor || undefined,
      keyword: filters.keyword || undefined,
    });
    logs.value = unwrapItems(response);
    total.value = Number(response?.data?.count || response?.count || logs.value.length);
    summary.value = response?.data?.summary || response?.summary || summary.value;
  } catch {
    notifyLoadError("后台操作日志");
  } finally {
    loading.value = false;
  }
}

function resetFilters() {
  filters.module = "";
  filters.actor = "";
  filters.keyword = "";
  void loadLogs();
}

function moduleLabel(value: string) {
  return (
    {
      users: "用户管理",
      recipes: "菜谱管理",
      community: "社区审核",
      reports: "运营复核",
    }[value] || value
  );
}

function moduleTagType(value: string) {
  return (
    {
      users: "danger",
      recipes: "warning",
      community: "success",
      reports: "info",
    }[value] || "info"
  );
}

function formatDateTime(value?: string) {
  if (!value) return "暂无";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "暂无";
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatChangeValue(value: unknown) {
  if (value === null || value === undefined || value === "") return "空";
  if (Array.isArray(value)) return value.length ? value.join("、") : "空";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function buildMetaLine(log: Record<string, any>) {
  const target = log.target_label ? `对象：${log.target_label}` : "对象：未命名";
  const action = log.action ? `动作：${log.action}` : "";
  return [target, action].filter(Boolean).join(" · ");
}
</script>

<style scoped>
.admin-operation-logs {
  gap: 18px;
}

.head-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.ops-alert-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.ops-alert-card {
  display: grid;
  gap: 6px;
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background:
    linear-gradient(135deg, rgba(252, 254, 255, 0.96), rgba(242, 248, 252, 0.94)),
    radial-gradient(circle at top right, rgba(87, 181, 231, 0.12), transparent 34%);
}

.ops-alert-card span {
  color: #638295;
  font-size: 12px;
}

.ops-alert-card strong {
  color: #173042;
  font-size: 28px;
}

.ops-alert-card p {
  margin: 0;
  color: #557383;
  line-height: 1.6;
}

.console-card {
  display: grid;
  gap: 16px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
}

.card-head h3 {
  margin: 0;
  font-size: 20px;
  color: #173042;
}

.card-head p {
  margin: 6px 0 0;
  color: #5b7888;
  line-height: 1.65;
}

.toolbar-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.table-meta {
  color: #6c8796;
  font-size: 13px;
}

.log-list {
  display: grid;
  gap: 14px;
}

.log-item {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: 20px;
  border: 1px solid rgba(18, 43, 56, 0.08);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(244, 249, 252, 0.95)),
    radial-gradient(circle at top right, rgba(88, 194, 255, 0.08), transparent 34%);
}

.log-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 14px;
  align-items: start;
}

.log-topline {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 6px;
}

.log-head strong {
  color: #173042;
  font-size: 18px;
}

.log-head p,
.log-topline span,
.log-actor span {
  margin: 0;
  color: #648190;
}

.log-actor {
  min-width: 104px;
  text-align: right;
}

.log-actor strong {
  display: block;
  margin-top: 6px;
}

.change-list {
  display: grid;
  gap: 10px;
}

.change-item {
  display: grid;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(241, 248, 251, 0.92);
  border: 1px solid rgba(18, 43, 56, 0.06);
}

.change-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.change-head strong {
  color: #173042;
  font-size: 14px;
}

.change-head span {
  color: #6a8797;
  font-size: 12px;
}

.change-values {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.change-values div {
  display: grid;
  gap: 6px;
  padding: 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.88);
}

.change-values span {
  color: #6d8794;
  font-size: 12px;
}

.change-values strong {
  color: #173042;
  font-size: 14px;
  word-break: break-word;
}

.change-empty {
  color: #698595;
  font-size: 13px;
}

@media (max-width: 1080px) {
  .toolbar-grid,
  .ops-alert-strip,
  .change-values {
    grid-template-columns: 1fr;
  }

  .log-head {
    grid-template-columns: 1fr;
  }

  .log-actor {
    text-align: left;
  }
}
</style>
