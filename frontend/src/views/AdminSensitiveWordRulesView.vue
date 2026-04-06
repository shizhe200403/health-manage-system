<template>
  <section class="page admin-sensitive-rules">
    <div class="head">
      <div>
        <p class="tag">Community Safety</p>
        <h2>敏感词管理</h2>
      </div>
      <div class="head-actions">
        <CompactHint tone="warm" title="敏感词规则" description="这里负责维护社区内容规则。屏蔽词会自动打星，拦截词会直接拒绝提交。" />
        <el-button plain @click="resetFilters">重置筛选</el-button>
        <el-button type="primary" :loading="loadingRules" @click="loadRules">刷新规则</el-button>
        <el-button plain @click="openEditor()">新增规则</el-button>
        <el-button plain @click="router.push('/ops/community')">回社区审核</el-button>
      </div>
    </div>

    <PageStateBlock
      v-if="auth.isAuthenticated && !auth.user"
      tone="loading"
      title="正在确认后台身份"
      description="稍等一下，正在确认你的账号权限。"
      compact
    />
    <PageStateBlock
      v-else-if="!hasOpsUser"
      tone="error"
      title="当前账号没有后台权限"
      description="敏感词管理只开放给后台管理账号，如果你需要权限可以联系超管。"
      action-label="回到首页"
      @action="router.push('/')"
    />
    <template v-else>
      <CollectionSkeleton v-if="showSkeleton" variant="list" :card-count="4" />
      <RefreshFrame v-else :active="loadingRules" label="正在同步敏感词规则">
        <div class="summary-grid">
          <article v-spotlight>
            <span>总规则数</span>
            <strong>{{ rules.length }}</strong>
            <p>当前筛选下可见的全部规则。</p>
          </article>
          <article v-spotlight>
            <span>屏蔽替换</span>
            <strong>{{ maskRuleCount }}</strong>
            <p>命中后会自动打星保存，不会直接拦截提交。</p>
          </article>
          <article v-spotlight>
            <span>直接拦截</span>
            <strong>{{ blockRuleCount }}</strong>
            <p>命中后会直接拒绝帖子或评论提交。</p>
          </article>
          <article v-spotlight>
            <span>启用中</span>
            <strong>{{ activeRuleCount }}</strong>
            <p>只有启用中的规则才会参与实际过滤。</p>
          </article>
        </div>

        <article class="card filter-card" v-spotlight>
          <div class="card-head">
            <div>
              <div class="section-title-row">
                <h3>筛选与维护</h3>
                <CompactHint description="先用关键词、动作和启用状态缩小范围，再决定是编辑规则还是直接停用。" />
              </div>
            </div>
          </div>
          <div class="toolbar-grid">
            <el-input v-model.trim="filters.keyword" placeholder="搜索敏感词或备注" clearable @keyup.enter="loadRules" />
            <el-select v-model="filters.action" clearable placeholder="处理动作">
              <el-option label="屏蔽替换" value="mask" />
              <el-option label="直接拦截" value="block" />
            </el-select>
            <el-select v-model="filters.isActive" clearable placeholder="启用状态">
              <el-option label="启用中" value="true" />
              <el-option label="已停用" value="false" />
            </el-select>
            <el-button type="primary" :loading="loadingRules" @click="loadRules">应用筛选</el-button>
          </div>
          <div class="filter-summary-strip">
            <span v-for="item in filterSummary" :key="item" class="filter-summary-chip">{{ item }}</span>
          </div>
        </article>

        <article class="card table-card" v-spotlight>
          <div class="card-head">
            <div>
              <div class="section-title-row">
                <h3>规则列表</h3>
                <CompactHint description="短词更容易误伤，强拦截词更需要谨慎。备注里最好写清楚为什么需要这条规则。" />
              </div>
            </div>
            <div class="card-head-actions">
              <el-button plain @click="openEditor()">新增规则</el-button>
            </div>
          </div>

          <el-table :data="rules" stripe class="moderation-table" empty-text="当前筛选下没有规则">
            <el-table-column label="敏感词" min-width="180">
              <template #default="{ row }">
                <div class="rule-word-cell">
                  <strong>{{ row.word }}</strong>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="动作" width="120">
              <template #default="{ row }">
                <el-tag :type="row.action === 'block' ? 'danger' : 'warning'" effect="light">
                  {{ row.action === "block" ? "直接拦截" : "屏蔽替换" }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="110">
              <template #default="{ row }">
                <el-tag :type="row.is_active ? 'success' : 'info'" effect="light">
                  {{ row.is_active ? "启用中" : "已停用" }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="备注" min-width="220">
              <template #default="{ row }">
                <span class="rule-note">{{ row.note || "暂无备注" }}</span>
              </template>
            </el-table-column>
            <el-table-column label="最近更新" width="170">
              <template #default="{ row }">
                <span>{{ formatDateTime(row.updated_at) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" fixed="right" width="220">
              <template #default="{ row }">
                <div class="rule-actions">
                  <el-button text type="primary" @click="openEditor(row)">编辑</el-button>
                  <el-button
                    text
                    :type="row.is_active ? 'warning' : 'success'"
                    :loading="savingRuleId === row.id"
                    @click="toggleRule(row)"
                  >
                    {{ row.is_active ? "停用" : "启用" }}
                  </el-button>
                  <el-button text type="danger" :loading="deletingRuleId === row.id" @click="removeRule(row)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </article>
      </RefreshFrame>
    </template>

    <el-dialog v-model="editorOpen" :title="editingRuleId ? '编辑敏感词规则' : '新增敏感词规则'" width="520px">
      <el-form label-position="top" class="drawer-form">
        <el-form-item label="敏感词">
          <el-input v-model.trim="draft.word" placeholder="例如：赌博" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="处理动作">
              <el-select v-model="draft.action" style="width: 100%">
                <el-option label="屏蔽替换" value="mask" />
                <el-option label="直接拦截" value="block" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="启用状态">
              <el-select v-model="draft.is_active" style="width: 100%">
                <el-option label="启用中" :value="true" />
                <el-option label="已停用" :value="false" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model.trim="draft.note" type="textarea" :rows="4" placeholder="说明这条规则为什么存在，便于后续复核。" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button plain @click="editorOpen = false">取消</el-button>
        <el-button type="primary" :loading="savingEditor" @click="saveRule">保存</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { ElMessageBox } from "element-plus";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import CompactHint from "../components/CompactHint.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import {
  createAdminSensitiveWordRule,
  deleteAdminSensitiveWordRule,
  listAdminSensitiveWordRules,
  updateAdminSensitiveWordRule,
  type AdminSensitiveWordRule,
} from "../api/adminContent";
import { hasOpsAccess } from "../lib/opsAccess";
import { extractApiErrorMessage, notifyActionSuccess, notifyErrorMessage, notifyLoadError } from "../lib/feedback";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();

const loadingRules = ref(false);
const rules = ref<AdminSensitiveWordRule[]>([]);
const editorOpen = ref(false);
const editingRuleId = ref<number | null>(null);
const savingEditor = ref(false);
const savingRuleId = ref<number | null>(null);
const deletingRuleId = ref<number | null>(null);

const filters = reactive({
  keyword: "",
  action: "",
  isActive: "",
});

const draft = reactive({
  word: "",
  action: "mask" as "mask" | "block",
  is_active: true,
  note: "",
});

const hasOpsUser = computed(() => hasOpsAccess(auth.user));
const showSkeleton = computed(() => loadingRules.value && !rules.value.length);
const maskRuleCount = computed(() => rules.value.filter((item) => item.action === "mask").length);
const blockRuleCount = computed(() => rules.value.filter((item) => item.action === "block").length);
const activeRuleCount = computed(() => rules.value.filter((item) => item.is_active).length);
const filterSummary = computed(() => {
  const items = [];
  if (filters.keyword) items.push(`搜索：${filters.keyword}`);
  if (filters.action) items.push(`动作：${filters.action === "block" ? "直接拦截" : "屏蔽替换"}`);
  if (filters.isActive) items.push(`状态：${filters.isActive === "true" ? "启用中" : "已停用"}`);
  return items.length ? items : ["当前无额外筛选"];
});

watch(
  hasOpsUser,
  (value) => {
    if (value) {
      void loadRules();
    }
  },
  { immediate: true },
);

function formatDateTime(value?: string) {
  if (!value) return "刚刚";
  return value.replace("T", " ").slice(0, 16);
}

function resetDraft() {
  editingRuleId.value = null;
  draft.word = "";
  draft.action = "mask";
  draft.is_active = true;
  draft.note = "";
}

function resetFilters() {
  filters.keyword = "";
  filters.action = "";
  filters.isActive = "";
  void loadRules();
}

async function loadRules() {
  if (!hasOpsUser.value) return;
  loadingRules.value = true;
  try {
    const response = await listAdminSensitiveWordRules({
      keyword: filters.keyword || undefined,
      action: filters.action || undefined,
      is_active: filters.isActive || undefined,
    });
    rules.value = response.data?.items ?? [];
  } catch {
    notifyLoadError("敏感词规则");
  } finally {
    loadingRules.value = false;
  }
}

function openEditor(rule?: AdminSensitiveWordRule) {
  if (!rule) {
    resetDraft();
    editorOpen.value = true;
    return;
  }
  editingRuleId.value = rule.id;
  draft.word = rule.word;
  draft.action = rule.action;
  draft.is_active = rule.is_active;
  draft.note = rule.note || "";
  editorOpen.value = true;
}

async function saveRule() {
  if (!draft.word.trim()) {
    notifyErrorMessage("敏感词不能为空");
    return;
  }

  savingEditor.value = true;
  try {
    const payload = {
      word: draft.word.trim(),
      action: draft.action,
      is_active: draft.is_active,
      note: draft.note.trim(),
    };
    if (editingRuleId.value) {
      await updateAdminSensitiveWordRule(editingRuleId.value, payload);
      notifyActionSuccess("敏感词规则已更新");
    } else {
      await createAdminSensitiveWordRule(payload);
      notifyActionSuccess("敏感词规则已新增");
    }
    editorOpen.value = false;
    resetDraft();
    await loadRules();
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "保存敏感词规则失败"));
  } finally {
    savingEditor.value = false;
  }
}

async function toggleRule(rule: AdminSensitiveWordRule) {
  savingRuleId.value = rule.id;
  try {
    await updateAdminSensitiveWordRule(rule.id, { is_active: !rule.is_active });
    notifyActionSuccess(rule.is_active ? "规则已停用" : "规则已启用");
    await loadRules();
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "更新规则状态失败"));
  } finally {
    savingRuleId.value = null;
  }
}

async function removeRule(rule: AdminSensitiveWordRule) {
  try {
    await ElMessageBox.confirm(`确认删除敏感词规则「${rule.word}」？`, "删除规则", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }

  deletingRuleId.value = rule.id;
  try {
    await deleteAdminSensitiveWordRule(rule.id);
    notifyActionSuccess("敏感词规则已删除");
    await loadRules();
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "删除敏感词规则失败"));
  } finally {
    deletingRuleId.value = null;
  }
}
</script>

<style scoped>
.admin-sensitive-rules {
  display: grid;
  gap: 16px;
}

.rule-word-cell strong {
  font-size: 15px;
  color: #173042;
}

.rule-note {
  color: #476072;
  line-height: 1.6;
}

.rule-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

@media (max-width: 768px) {
  .rule-actions {
    flex-wrap: wrap;
    gap: 6px;
  }
}
</style>
