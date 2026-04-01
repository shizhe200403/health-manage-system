<template>
  <section class="page admin-dashboard">
    <div class="head">
      <div>
        <p class="tag">Admin Console</p>
        <h2>后台总览</h2>
        <p class="desc">先看今天最值得处理的管理动作，再进入具体模块，避免后台也变成信息堆叠页。</p>
      </div>
      <div class="head-actions">
        <RouterLink class="ghost-link" to="/ops/logs">进入操作日志</RouterLink>
        <RouterLink class="ghost-link" to="/ops/reports">进入运营复核</RouterLink>
        <RouterLink class="ghost-link" to="/ops/community">进入社区审核</RouterLink>
        <RouterLink class="ghost-link" to="/ops/recipes">进入菜谱管理</RouterLink>
        <RouterLink class="ghost-link" to="/ops/users">进入用户管理</RouterLink>
        <RouterLink class="ghost-link ghost-link-soft" to="/">回前台首页</RouterLink>
      </div>
    </div>

    <PageStateBlock
      v-if="auth.isAuthenticated && !auth.user"
      tone="loading"
      title="正在确认管理员身份"
      description="先把当前账号权限拉齐，再展开后台总览。"
      compact
    />
    <PageStateBlock
      v-else-if="!isAdminUser"
      tone="error"
      title="当前账号没有后台权限"
      description="后台总览只对管理员开放，普通账号不会进入这里。"
      action-label="回到首页"
      @action="router.push('/')"
    />
    <template v-else>
      <CollectionSkeleton v-if="loading && !recentUsers.length" variant="dashboard" :card-count="4" />
      <RefreshFrame v-else :active="loading" label="正在同步后台总览与用户样本">
        <div class="ops-alert-strip">
          <article v-for="alert in opsAlerts" :key="alert.label" class="ops-alert-card" v-spotlight>
            <span>{{ alert.label }}</span>
            <strong>{{ alert.value }}</strong>
            <p>{{ alert.copy }}</p>
          </article>
        </div>

        <div class="summary-grid">
          <article v-spotlight>
            <span>账号总量</span>
            <strong>{{ totalUsers }}</strong>
            <p>全部注册用户数量，适合先把整体规模看清楚。</p>
          </article>
          <article v-spotlight>
            <span>最近样本</span>
            <strong>{{ recentUsers.length }}</strong>
            <p>后台首页默认抓取最近一批账号，用来快速判断是否有异常聚集。</p>
          </article>
          <article v-spotlight>
            <span>样本中停用</span>
            <strong>{{ disabledInSample }}</strong>
            <p>这些账号值得优先确认是人工停用还是资料异常导致。</p>
          </article>
          <article v-spotlight>
            <span>样本中资料完整</span>
            <strong>{{ profileReadyInSample }}</strong>
            <p>档案完整度较高时，系统推荐和个性化建议会更稳。</p>
          </article>
        </div>

        <div class="admin-grid">
          <article class="card console-card" v-spotlight>
            <div class="card-head">
              <div>
                <h3>今日值守建议</h3>
                <p>后台先处理最影响真实用户体验的问题，不要一上来就散到所有模块。</p>
              </div>
            </div>
            <div class="ops-list">
              <article v-for="tip in adminFocusTips" :key="tip.title" class="ops-item">
                <strong>{{ tip.title }}</strong>
                <p>{{ tip.copy }}</p>
                <RouterLink :to="tip.to">{{ tip.cta }}</RouterLink>
              </article>
            </div>
          </article>

          <article class="card console-card" v-spotlight>
            <div class="card-head">
              <div>
                <h3>最近账号样本</h3>
                <p>默认拉最近注册或最近活跃的一批账号，适合先看状态分布与资料质量。</p>
              </div>
            </div>
            <PageStateBlock
              v-if="!recentUsers.length"
              tone="empty"
              title="暂时没有可展示的账号样本"
              description="可以稍后刷新，或直接进入用户管理查看完整列表。"
              compact
            />
            <div v-else class="sample-list">
              <article v-for="user in recentUsers" :key="user.id" class="sample-item">
                <div>
                  <strong>{{ user.nickname || user.username }}</strong>
                  <span>@{{ user.username }}</span>
                </div>
                <div class="sample-meta">
                  <el-tag size="small" :type="roleTagType(user.role)" effect="light">{{ roleLabel(user.role) }}</el-tag>
                  <el-tag size="small" :type="statusTagType(user.status)" effect="light">{{ statusLabel(user.status) }}</el-tag>
                  <span>档案 {{ user.profile_completion }}%</span>
                </div>
              </article>
            </div>
          </article>

          <article class="card console-card quick-actions" v-spotlight>
            <div class="card-head">
              <div>
                <h3>后台快捷动作</h3>
                <p>先把后台真正高频的动作收在这里，后面再逐步拆出更多模块。</p>
              </div>
            </div>
            <RouterLink class="action-link action-link-primary" to="/ops/users">
              <strong>用户管理</strong>
              <span>查看账号状态、角色边界、资料完整度与健康约束。</span>
            </RouterLink>
            <RouterLink class="action-link" to="/ops/logs">
              <strong>操作日志</strong>
              <span>回看后台最近是谁改了什么，避免处理结果脱离过程。</span>
            </RouterLink>
            <RouterLink class="action-link" to="/ops/reports">
              <strong>运营复核</strong>
              <span>看整体活跃度、内容处理节奏和报表任务健康度，判断后台当前最该补哪里。</span>
            </RouterLink>
            <RouterLink class="action-link" to="/ops/community">
              <strong>社区审核</strong>
              <span>处理帖子审核、举报进度和评论隐藏，减少风险内容继续暴露。</span>
            </RouterLink>
            <RouterLink class="action-link" to="/ops/recipes">
              <strong>菜谱管理</strong>
              <span>复核菜谱审核状态、信息完整度与是否适合继续发布。</span>
            </RouterLink>
          </article>
        </div>

        <div class="admin-lower-grid">
          <article class="card console-card module-card" v-spotlight>
            <div class="card-head">
              <div>
                <h3>后台模块视图</h3>
                <p>先把已经成型、下一步要做、还在前台借道处理的模块分清楚，后台路线才会清晰。</p>
              </div>
            </div>
            <div class="module-list">
              <article v-for="module in moduleCards" :key="module.title" class="module-item" :class="`module-item-${module.tone}`">
                <div>
                  <span class="module-state">{{ module.state }}</span>
                  <strong>{{ module.title }}</strong>
                </div>
                <p>{{ module.copy }}</p>
                <RouterLink :to="module.to">{{ module.cta }}</RouterLink>
              </article>
            </div>
          </article>

          <article class="card console-card" v-spotlight>
            <div class="card-head">
              <div>
                <h3>样本分布</h3>
                <p>用最近一批账号快速感知后台今天是偏权限问题、资料问题，还是正常维护节奏。</p>
              </div>
            </div>
            <div class="distribution-list">
              <article v-for="item in sampleBreakdown" :key="item.label" class="distribution-item">
                <div class="distribution-copy">
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.copy }}</span>
                </div>
                <div class="distribution-value">
                  <strong>{{ item.value }}</strong>
                  <small>{{ item.share }}</small>
                </div>
              </article>
            </div>
          </article>
        </div>
      </RefreshFrame>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import { listAdminUsers } from "../api/admin";
import { notifyLoadError } from "../lib/feedback";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();

const loading = ref(false);
const totalUsers = ref(0);
const recentUsers = ref<any[]>([]);

const isAdminUser = computed(() => Boolean(auth.user && (auth.user.role === "admin" || auth.user.is_superuser || auth.user.is_staff)));
const disabledInSample = computed(() => recentUsers.value.filter((item) => item.status === "disabled").length);
const profileReadyInSample = computed(() => recentUsers.value.filter((item) => Number(item.profile_completion || 0) >= 70).length);
const pendingInSample = computed(() => recentUsers.value.filter((item) => item.status === "pending").length);
const incompleteInSample = computed(() => recentUsers.value.filter((item) => Number(item.profile_completion || 0) < 70).length);
const flaggedInSample = computed(() => recentUsers.value.filter((item) => Array.isArray(item.health_flags) && item.health_flags.length > 0).length);
const sampleBase = computed(() => Math.max(recentUsers.value.length, 1));
const opsAlerts = computed(() => [
  {
    label: "待处理账号",
    value: pendingInSample.value,
    copy: pendingInSample.value > 0 ? "建议优先确认资料缺口与权限异常。" : "当前样本没有明显待处理堆积。",
  },
  {
    label: "资料待补齐",
    value: incompleteInSample.value,
    copy: incompleteInSample.value > 0 ? "这部分会直接影响个性化推荐准确度。" : "最近样本的资料质量整体比较稳定。",
  },
  {
    label: "健康标记",
    value: flaggedInSample.value,
    copy: flaggedInSample.value > 0 ? "这些账号值得留意推荐边界与风险提示。" : "当前样本暂时没有明显健康约束聚集。",
  },
]);
const adminFocusTips = computed(() => [
  {
    title: pendingInSample.value > 0 ? "先处理待处理账号" : "先把权限边界看清楚",
    copy: pendingInSample.value > 0
      ? `最近样本里还有 ${pendingInSample.value} 个待处理账号，先确认这些账号是资料不完整、权限异常还是需要人工介入。`
      : "这轮样本里没有明显的待处理堆积，先检查管理员与普通用户边界是否清晰。",
    cta: "去用户管理",
    to: "/ops/users",
  },
  {
    title: disabledInSample.value > 0 ? "复核停用状态是否合理" : "继续补齐资料质量视角",
    copy: disabledInSample.value > 0
      ? `最近样本里有 ${disabledInSample.value} 个停用账号，先确认是主动禁用还是误伤，再决定是否恢复。`
      : "停用账号不多时，优先把档案完整度、联系方式和角色信息看齐，后面排查会更快。",
    cta: "查看账号样本",
    to: "/ops/users",
  },
  {
    title: "保持前后台视角切换",
    copy: "后台看到的问题，最后都要回到前台用户链路验证一次，避免只在控制台里自洽。",
    cta: "回前台首页",
    to: "/",
  },
]);
const moduleCards = computed(() => [
  {
    state: "已成型",
    title: "用户管理",
    copy: "账号状态、角色边界、资料完整度与健康约束已经进入后台主线。",
    cta: "进入模块",
    to: "/ops/users",
    tone: "ready",
  },
  {
    state: "已成型",
    title: "操作日志",
    copy: "管理员处理用户、菜谱和社区内容的动作已经能沉淀下来，方便回看是谁改了什么。",
    cta: "进入模块",
    to: "/ops/logs",
    tone: "ready",
  },
  {
    state: "已成型",
    title: "运营复核",
    copy: "管理员已经能从后台看整体活跃、内容处理节奏和报表任务状态，不用再借道前台报表。",
    cta: "进入模块",
    to: "/ops/reports",
    tone: "ready",
  },
  {
    state: "已成型",
    title: "社区审核",
    copy: "帖子审核、举报处理和评论隐藏已经进入后台主线，适合下一步继续扩细。",
    cta: "进入模块",
    to: "/ops/community",
    tone: "ready",
  },
  {
    state: "已成型",
    title: "菜谱管理",
    copy: "菜谱状态、审核结论和内容质量现在已经纳入后台工作台主线。",
    cta: "进入模块",
    to: "/ops/recipes",
    tone: "ready",
  },
  {
    state: "下一步",
    title: "处理回放",
    copy: "下一轮更适合继续把日志做成按对象聚合的处理回放，而不只是时间流列表。",
    cta: "先看操作日志",
    to: "/ops/logs",
    tone: "next",
  },
]);
const sampleBreakdown = computed(() => [
  {
    label: "正常账号",
    value: recentUsers.value.filter((item) => item.status === "active").length,
    share: formatShare(recentUsers.value.filter((item) => item.status === "active").length, sampleBase.value),
    copy: "当前样本里保持正常状态的账号数量。",
  },
  {
    label: "管理员账号",
    value: recentUsers.value.filter((item) => item.role === "admin").length,
    share: formatShare(recentUsers.value.filter((item) => item.role === "admin").length, sampleBase.value),
    copy: "适合顺手确认管理权限是否收敛在合理范围内。",
  },
  {
    label: "资料未满 70%",
    value: incompleteInSample.value,
    share: formatShare(incompleteInSample.value, sampleBase.value),
    copy: "这部分会最直接拉低系统建议的针对性。",
  },
  {
    label: "有健康标记",
    value: flaggedInSample.value,
    share: formatShare(flaggedInSample.value, sampleBase.value),
    copy: "需要更关注推荐边界与饮食约束表达。",
  },
]);

onMounted(() => {
  if (isAdminUser.value) {
    void loadOverview();
  }
});

function unwrapListPayload(payload: any) {
  if (Array.isArray(payload?.data?.items)) return payload.data.items;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload)) return payload;
  return [];
}

async function loadOverview() {
  loading.value = true;
  try {
    const response = await listAdminUsers({ page: 1, page_size: 8 });
    recentUsers.value = unwrapListPayload(response);
    totalUsers.value = Number(response?.data?.count || response?.count || recentUsers.value.length);
  } catch {
    notifyLoadError("后台总览");
  } finally {
    loading.value = false;
  }
}

function roleLabel(value: string) {
  return (
    {
      user: "普通用户",
      admin: "管理员",
      auditor: "审核员",
    }[value] || value
  );
}

function statusLabel(value: string) {
  return (
    {
      active: "正常",
      disabled: "已停用",
      pending: "待处理",
    }[value] || value
  );
}

function roleTagType(value: string) {
  return (
    {
      admin: "danger",
      auditor: "warning",
      user: "info",
    }[value] || "info"
  );
}

function statusTagType(value: string) {
  return (
    {
      active: "success",
      disabled: "danger",
      pending: "warning",
    }[value] || "info"
  );
}

function formatShare(value: number, total: number) {
  return `${Math.round((value / total) * 100)}%`;
}
</script>

<style scoped>
.admin-dashboard {
  gap: 18px;
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

.head-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.ghost-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  padding: 0 16px;
  border-radius: 999px;
  text-decoration: none;
  font-weight: 700;
  color: #f3f7fb;
  background: linear-gradient(135deg, #173042, #28546b);
  box-shadow: 0 16px 28px rgba(11, 22, 35, 0.18);
}

.ghost-link-soft {
  color: #173042;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: none;
}

.admin-grid {
  display: grid;
  grid-template-columns: 1.25fr 1.1fr 0.95fr;
  gap: 16px;
}

.admin-lower-grid {
  display: grid;
  grid-template-columns: 1.25fr 1fr;
  gap: 16px;
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

.ops-list,
.sample-list,
.quick-actions {
  display: grid;
  gap: 12px;
}

.ops-item,
.sample-item,
.action-link {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(247, 251, 255, 0.92);
}

.module-list,
.distribution-list {
  display: grid;
  gap: 12px;
}

.module-item,
.distribution-item {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(247, 251, 255, 0.92);
}

.module-item {
  grid-template-columns: minmax(0, 1fr);
}

.module-item div {
  display: grid;
  gap: 6px;
}

.module-state {
  display: inline-flex;
  width: fit-content;
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.module-item strong,
.distribution-item strong {
  color: #173042;
  font-size: 15px;
}

.module-item p,
.distribution-copy span {
  margin: 0;
  color: #5b7888;
  line-height: 1.65;
}

.module-item a {
  color: #1f4f67;
  text-decoration: none;
  font-weight: 700;
}

.module-item-ready .module-state {
  background: rgba(34, 197, 94, 0.14);
  color: #178048;
}

.module-item-next .module-state {
  background: rgba(245, 158, 11, 0.14);
  color: #b56f00;
}

.module-item-cross .module-state {
  background: rgba(87, 181, 231, 0.14);
  color: #1f6286;
}

.distribution-item {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
}

.distribution-copy {
  display: grid;
  gap: 4px;
}

.distribution-value {
  display: grid;
  justify-items: end;
  gap: 4px;
}

.distribution-value small {
  color: #638295;
  font-size: 12px;
}

.ops-item strong,
.sample-item strong,
.action-link strong {
  color: #173042;
  font-size: 15px;
}

.ops-item p,
.action-link span {
  margin: 0;
  color: #5b7888;
  line-height: 1.65;
}

.ops-item a,
.action-link {
  text-decoration: none;
}

.ops-item a {
  color: #1f4f67;
  font-weight: 700;
}

.sample-item {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
}

.sample-item span {
  color: #5b7888;
  font-size: 13px;
}

.sample-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  align-items: center;
}

.action-link {
  color: inherit;
}

.action-link-primary {
  background: linear-gradient(135deg, rgba(23, 48, 66, 0.96), rgba(43, 83, 105, 0.92));
}

.action-link-primary strong,
.action-link-primary span {
  color: #f7fbff;
}

@media (max-width: 1080px) {
  .ops-alert-strip,
  .admin-grid,
  .admin-lower-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .head-actions,
  .sample-item,
  .sample-meta {
    grid-template-columns: 1fr;
    justify-content: flex-start;
  }

  .ghost-link {
    width: 100%;
  }

  .sample-item {
    align-items: flex-start;
  }
}
</style>
