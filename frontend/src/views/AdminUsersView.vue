<template>
  <section class="page admin-page">
    <div class="head">
      <div>
        <p class="tag">Admin</p>
        <h2>用户管理</h2>
        <p class="desc">先把账号状态、角色和资料情况看清楚，后续内容审核和问题排查才有抓手。</p>
      </div>
      <div class="head-actions">
        <el-button plain @click="resetFilters">重置筛选</el-button>
        <el-button type="primary" :loading="loadingUsers" @click="loadUsers">刷新列表</el-button>
      </div>
    </div>

    <PageStateBlock
      v-if="auth.isAuthenticated && !auth.user"
      tone="loading"
      title="正在确认管理员身份"
      description="先把当前账号权限核对清楚，再展开后台内容。"
      compact
    />
    <PageStateBlock
      v-else-if="!isAdminUser"
      tone="error"
      title="当前账号没有后台权限"
      description="用户管理只对管理员开放，普通账号不会显示这块后台能力。"
      action-label="回到首页"
      @action="router.push('/')"
    />
    <template v-else>
      <CollectionSkeleton v-if="loadingUsers && !users.length" variant="list" :card-count="5" />
      <RefreshFrame v-else :active="loadingUsers && !!users.length" label="正在同步用户列表与筛选结果">
        <div class="summary-grid">
          <article>
            <span>用户总数</span>
            <strong>{{ pagination.total }}</strong>
            <p>当前筛选条件下的账号总量。</p>
          </article>
          <article>
            <span>管理员</span>
            <strong>{{ adminCount }}</strong>
            <p>当前页中具备管理权限的账号数量。</p>
          </article>
          <article>
            <span>已停用</span>
            <strong>{{ disabledCount }}</strong>
            <p>适合优先检查这些账号是否需要恢复或保留禁用。</p>
          </article>
          <article>
            <span>资料较完整</span>
            <strong>{{ profileReadyCount }}</strong>
            <p>当前页档案完整度达到 70% 以上的用户数。</p>
          </article>
        </div>

        <div class="card filter-card">
          <div class="card-head">
            <div>
              <h3>筛选与搜索</h3>
              <p>先快速定位用户名、邮箱或手机号，再看角色和状态。</p>
            </div>
          </div>
          <div class="toolbar-grid">
            <el-input v-model.trim="filters.keyword" placeholder="搜索用户名 / 昵称 / 邮箱 / 手机号" clearable @keyup.enter="applyFilters" />
            <el-select v-model="filters.role" clearable placeholder="筛选角色">
              <el-option label="普通用户" value="user" />
              <el-option label="管理员" value="admin" />
              <el-option label="审核员" value="auditor" />
            </el-select>
            <el-select v-model="filters.status" clearable placeholder="筛选状态">
              <el-option label="正常" value="active" />
              <el-option label="已停用" value="disabled" />
              <el-option label="待处理" value="pending" />
            </el-select>
            <el-button type="primary" :loading="loadingUsers" @click="applyFilters">应用筛选</el-button>
          </div>
        </div>

        <div class="card table-card">
          <div class="card-head">
            <div>
              <h3>用户列表</h3>
              <p>默认按注册时间倒序展示，适合先处理最新注册或异常状态用户。</p>
            </div>
          </div>

          <el-table :data="users" stripe class="user-table" empty-text="当前筛选下没有用户">
            <el-table-column label="用户" min-width="200">
              <template #default="{ row }">
                <div class="user-cell">
                  <strong>{{ row.nickname || row.username }}</strong>
                  <span>@{{ row.username }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="联系方式" min-width="220">
              <template #default="{ row }">
                <div class="contact-cell">
                  <span>{{ row.email || "未填写邮箱" }}</span>
                  <span>{{ row.phone || "未填写手机号" }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="角色" width="120">
              <template #default="{ row }">
                <el-tag :type="roleTagType(row.role)" effect="light">{{ roleLabel(row.role) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="120">
              <template #default="{ row }">
                <el-tag :type="statusTagType(row.status)" effect="light">{{ statusLabel(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="档案完整度" width="140">
              <template #default="{ row }">
                <span>{{ row.profile_completion }}%</span>
              </template>
            </el-table-column>
            <el-table-column label="健康提示" min-width="180">
              <template #default="{ row }">
                <div class="flag-cell">
                  <el-tag v-for="item in row.health_flags" :key="item" size="small" type="warning" effect="plain">{{ item }}</el-tag>
                  <span v-if="!row.health_flags?.length" class="muted-copy">暂无特殊标记</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="最近登录" width="170">
              <template #default="{ row }">
                <span>{{ formatDateTime(row.last_login) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" fixed="right" width="140">
              <template #default="{ row }">
                <el-button text type="primary" @click="openUserDrawer(row.id)">查看并编辑</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="table-footer">
            <span>当前第 {{ pagination.page }} 页，共 {{ pagination.total }} 个账号。</span>
            <el-pagination
              background
              layout="prev, pager, next"
              :current-page="pagination.page"
              :page-size="pagination.pageSize"
              :total="pagination.total"
              @current-change="handlePageChange"
            />
          </div>
        </div>
      </RefreshFrame>

      <el-drawer v-model="drawerOpen" size="560px" :title="drawerTitle" destroy-on-close>
        <PageStateBlock
          v-if="detailLoading"
          tone="loading"
          title="正在加载用户详情"
          description="把这个账号的资料、状态和健康约束拉齐后再允许编辑。"
          compact
        />
        <PageStateBlock
          v-else-if="!selectedUser"
          tone="empty"
          title="还没有选中用户"
          description="从列表里点开一个账号，右侧就会展开详细资料。"
          compact
        />
        <template v-else>
          <div class="drawer-summary">
            <article>
              <span>注册时间</span>
              <strong>{{ formatDateTime(selectedUser.date_joined) }}</strong>
            </article>
            <article>
              <span>最近登录</span>
              <strong>{{ formatDateTime(selectedUser.last_login) }}</strong>
            </article>
            <article>
              <span>当前角色</span>
              <strong>{{ roleLabel(accountDraft.role) }}</strong>
            </article>
          </div>

          <el-form label-position="top" class="drawer-form">
            <div class="drawer-section">
              <div class="drawer-section-head">
                <strong>账号信息</strong>
                <span>角色、状态和联系方式优先在这里处理。</span>
              </div>
              <el-row :gutter="12">
                <el-col :span="12">
                  <el-form-item label="用户名">
                    <el-input v-model.trim="accountDraft.username" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="昵称">
                    <el-input v-model.trim="accountDraft.nickname" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="邮箱">
                    <el-input v-model.trim="accountDraft.email" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="手机号">
                    <el-input v-model.trim="accountDraft.phone" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="角色">
                    <el-select v-model="accountDraft.role" style="width: 100%">
                      <el-option label="普通用户" value="user" />
                      <el-option label="管理员" value="admin" />
                      <el-option label="审核员" value="auditor" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="状态">
                    <el-select v-model="accountDraft.status" style="width: 100%">
                      <el-option label="正常" value="active" />
                      <el-option label="已停用" value="disabled" />
                      <el-option label="待处理" value="pending" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="个性签名">
                <el-input v-model.trim="accountDraft.signature" type="textarea" :rows="2" />
              </el-form-item>
            </div>

            <div class="drawer-section">
              <div class="drawer-section-head">
                <strong>生活方式</strong>
                <span>这些信息会直接影响推荐、目标和今日建议的判断。</span>
              </div>
              <el-row :gutter="12">
                <el-col :span="8">
                  <el-form-item label="身高(cm)">
                    <el-input-number v-model="profileDraft.height_cm" :min="0" :precision="1" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="体重(kg)">
                    <el-input-number v-model="profileDraft.weight_kg" :min="0" :precision="1" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="目标体重(kg)">
                    <el-input-number v-model="profileDraft.target_weight_kg" :min="0" :precision="1" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="活动水平">
                    <el-select v-model="profileDraft.activity_level" style="width: 100%">
                      <el-option label="久坐为主" value="low" />
                      <el-option label="轻度活动" value="medium" />
                      <el-option label="经常运动" value="high" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="饮食偏好">
                    <el-select v-model="profileDraft.meal_preference" style="width: 100%">
                      <el-option label="家常清淡" value="light_home" />
                      <el-option label="高蛋白优先" value="high_protein" />
                      <el-option label="低脂控能量" value="low_fat" />
                      <el-option label="省时方便" value="fast_easy" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="饮食类型">
                    <el-select v-model="profileDraft.diet_type" style="width: 100%">
                      <el-option label="均衡饮食" value="balanced" />
                      <el-option label="高蛋白" value="high_protein" />
                      <el-option label="低碳水" value="low_carb" />
                      <el-option label="素食" value="vegetarian" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="职业">
                    <el-input v-model.trim="profileDraft.occupation" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="外食频率">
                <el-switch v-model="profileDraft.is_outdoor_eating_frequent" active-text="经常外食" inactive-text="以家里吃饭为主" />
              </el-form-item>
            </div>

            <div class="drawer-section">
              <div class="drawer-section-head">
                <strong>健康约束</strong>
                <span>这些约束会直接影响推荐和风险提醒，不适合留空太久。</span>
              </div>
              <div class="toggle-grid">
                <el-checkbox v-model="healthDraft.has_diabetes">糖尿病</el-checkbox>
                <el-checkbox v-model="healthDraft.has_hypertension">高血压</el-checkbox>
                <el-checkbox v-model="healthDraft.has_hyperlipidemia">高血脂</el-checkbox>
                <el-checkbox v-model="healthDraft.has_allergy">存在过敏项</el-checkbox>
              </div>
              <el-form-item label="过敏标签">
                <el-select
                  v-model="healthDraft.allergy_tags"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  style="width: 100%"
                  placeholder="输入后回车，可添加多个"
                >
                  <el-option v-for="item in allergyOptions" :key="item" :label="item" :value="item" />
                </el-select>
              </el-form-item>
              <el-form-item label="忌口标签">
                <el-select
                  v-model="healthDraft.avoid_food_tags"
                  multiple
                  filterable
                  allow-create
                  default-first-option
                  style="width: 100%"
                  placeholder="输入后回车，可添加多个"
                >
                  <el-option v-for="item in avoidFoodOptions" :key="item" :label="item" :value="item" />
                </el-select>
              </el-form-item>
              <el-form-item label="备注">
                <el-input v-model.trim="healthDraft.notes" type="textarea" :rows="3" />
              </el-form-item>
            </div>
          </el-form>

          <div class="drawer-actions">
            <el-button plain @click="drawerOpen = false">取消</el-button>
            <el-button type="primary" :loading="savingUser" @click="saveUser">保存修改</el-button>
          </div>
        </template>
      </el-drawer>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import { getAdminUserDetail, listAdminUsers, updateAdminUser } from "../api/admin";
import { extractApiErrorMessage, notifyActionSuccess, notifyErrorMessage, notifyLoadError } from "../lib/feedback";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();

const loadingUsers = ref(false);
const detailLoading = ref(false);
const savingUser = ref(false);
const drawerOpen = ref(false);
const users = ref<any[]>([]);
const selectedUser = ref<any | null>(null);

const filters = reactive({
  keyword: "",
  role: "",
  status: "",
});

const pagination = reactive({
  page: 1,
  pageSize: 12,
  total: 0,
});

const accountDraft = reactive({
  username: "",
  nickname: "",
  email: "",
  phone: "",
  signature: "",
  role: "user",
  status: "active",
});

const profileDraft = reactive({
  height_cm: null as number | null,
  weight_kg: null as number | null,
  target_weight_kg: null as number | null,
  activity_level: "medium",
  meal_preference: "light_home",
  diet_type: "balanced",
  occupation: "",
  is_outdoor_eating_frequent: false,
});

const healthDraft = reactive({
  has_diabetes: false,
  has_hypertension: false,
  has_hyperlipidemia: false,
  has_allergy: false,
  allergy_tags: [] as string[],
  avoid_food_tags: [] as string[],
  notes: "",
});

const allergyOptions = ["花生", "牛奶", "鸡蛋", "海鲜", "坚果"];
const avoidFoodOptions = ["辛辣", "油炸", "高糖", "高盐", "酒精"];

const isAdminUser = computed(() => Boolean(auth.user && (auth.user.role === "admin" || auth.user.is_superuser)));
const adminCount = computed(() => users.value.filter((item) => item.role === "admin").length);
const disabledCount = computed(() => users.value.filter((item) => item.status === "disabled").length);
const profileReadyCount = computed(() => users.value.filter((item) => Number(item.profile_completion || 0) >= 70).length);
const drawerTitle = computed(() => (selectedUser.value ? `编辑用户：${selectedUser.value.nickname || selectedUser.value.username}` : "编辑用户"));

onMounted(() => {
  if (isAdminUser.value) {
    void loadUsers();
  }
});

watch(
  isAdminUser,
  (value) => {
    if (value && !users.value.length) {
      void loadUsers();
    }
  },
  { immediate: false },
);

function unwrapListPayload(payload: any) {
  if (Array.isArray(payload?.data?.items)) return payload.data.items;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload)) return payload;
  return [];
}

function resetDrafts() {
  Object.assign(accountDraft, {
    username: "",
    nickname: "",
    email: "",
    phone: "",
    signature: "",
    role: "user",
    status: "active",
  });
  Object.assign(profileDraft, {
    height_cm: null,
    weight_kg: null,
    target_weight_kg: null,
    activity_level: "medium",
    meal_preference: "light_home",
    diet_type: "balanced",
    occupation: "",
    is_outdoor_eating_frequent: false,
  });
  Object.assign(healthDraft, {
    has_diabetes: false,
    has_hypertension: false,
    has_hyperlipidemia: false,
    has_allergy: false,
    allergy_tags: [],
    avoid_food_tags: [],
    notes: "",
  });
}

function fillDrafts(user: Record<string, any>) {
  Object.assign(accountDraft, {
    username: user.username || "",
    nickname: user.nickname || "",
    email: user.email || "",
    phone: user.phone || "",
    signature: user.signature || "",
    role: user.role || "user",
    status: user.status || "active",
  });
  Object.assign(profileDraft, {
    height_cm: user.profile?.height_cm ? Number(user.profile.height_cm) : null,
    weight_kg: user.profile?.weight_kg ? Number(user.profile.weight_kg) : null,
    target_weight_kg: user.profile?.target_weight_kg ? Number(user.profile.target_weight_kg) : null,
    activity_level: user.profile?.activity_level || "medium",
    meal_preference: user.profile?.meal_preference || "light_home",
    diet_type: user.profile?.diet_type || "balanced",
    occupation: user.profile?.occupation || "",
    is_outdoor_eating_frequent: Boolean(user.profile?.is_outdoor_eating_frequent),
  });
  Object.assign(healthDraft, {
    has_diabetes: Boolean(user.health_condition?.has_diabetes),
    has_hypertension: Boolean(user.health_condition?.has_hypertension),
    has_hyperlipidemia: Boolean(user.health_condition?.has_hyperlipidemia),
    has_allergy: Boolean(user.health_condition?.has_allergy),
    allergy_tags: Array.isArray(user.health_condition?.allergy_tags) ? [...user.health_condition.allergy_tags] : [],
    avoid_food_tags: Array.isArray(user.health_condition?.avoid_food_tags) ? [...user.health_condition.avoid_food_tags] : [],
    notes: user.health_condition?.notes || "",
  });
}

async function loadUsers() {
  if (!isAdminUser.value) return;

  loadingUsers.value = true;
  try {
    const response = await listAdminUsers({
      page: pagination.page,
      page_size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      role: filters.role || undefined,
      status: filters.status || undefined,
    });
    users.value = unwrapListPayload(response);
    pagination.total = Number(response?.data?.count || 0);
  } catch {
    notifyLoadError("用户列表");
  } finally {
    loadingUsers.value = false;
  }
}

function applyFilters() {
  pagination.page = 1;
  void loadUsers();
}

function resetFilters() {
  filters.keyword = "";
  filters.role = "";
  filters.status = "";
  pagination.page = 1;
  void loadUsers();
}

function handlePageChange(page: number) {
  pagination.page = page;
  void loadUsers();
}

async function openUserDrawer(userId: number) {
  drawerOpen.value = true;
  detailLoading.value = true;
  selectedUser.value = null;
  resetDrafts();

  try {
    const response = await getAdminUserDetail(userId);
    selectedUser.value = response?.data ?? null;
    if (selectedUser.value) {
      fillDrafts(selectedUser.value);
    }
  } catch {
    notifyLoadError("用户详情");
    drawerOpen.value = false;
  } finally {
    detailLoading.value = false;
  }
}

async function saveUser() {
  if (!selectedUser.value) return;

  savingUser.value = true;
  try {
    const response = await updateAdminUser(selectedUser.value.id, {
      account: { ...accountDraft },
      profile: { ...profileDraft },
      health_condition: { ...healthDraft },
    });
    selectedUser.value = response?.data ?? null;
    if (selectedUser.value) {
      fillDrafts(selectedUser.value);
    }
    notifyActionSuccess("用户资料已经更新");
    await auth.fetchMe();
    await loadUsers();
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "用户资料这次没有更新成功"));
  } finally {
    savingUser.value = false;
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
</script>

<style scoped>
.admin-page {
  gap: 18px;
}

.head-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-card,
.table-card {
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
  grid-template-columns: minmax(220px, 1.8fr) repeat(2, minmax(160px, 0.9fr)) auto;
  gap: 12px;
}

.user-table {
  width: 100%;
}

.user-cell,
.contact-cell {
  display: grid;
  gap: 4px;
}

.user-cell strong {
  color: #173042;
}

.user-cell span,
.contact-cell span,
.muted-copy {
  color: #5b7888;
  font-size: 13px;
}

.flag-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  color: #5b7888;
  font-size: 13px;
}

.drawer-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 18px;
}

.drawer-summary article {
  padding: 14px;
  border-radius: 16px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.08);
  display: grid;
  gap: 6px;
}

.drawer-summary span {
  color: #5b7888;
  font-size: 12px;
}

.drawer-summary strong {
  color: #173042;
  font-size: 15px;
}

.drawer-form {
  display: grid;
  gap: 18px;
}

.drawer-section {
  padding: 18px;
  border-radius: 18px;
  background: rgba(247, 251, 255, 0.94);
  border: 1px solid rgba(16, 34, 42, 0.08);
}

.drawer-section-head {
  display: grid;
  gap: 6px;
  margin-bottom: 14px;
}

.drawer-section-head strong {
  color: #173042;
  font-size: 16px;
}

.drawer-section-head span {
  color: #5b7888;
  font-size: 13px;
  line-height: 1.6;
}

.toggle-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.drawer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
}

@media (max-width: 960px) {
  .toolbar-grid {
    grid-template-columns: 1fr;
  }

  .drawer-summary {
    grid-template-columns: 1fr;
  }

  .toggle-grid {
    grid-template-columns: 1fr;
  }
}
</style>
