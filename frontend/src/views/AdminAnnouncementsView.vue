<template>
  <section class="page admin-announcements">
    <div class="head">
      <div>
        <p class="tag">Announcement Center</p>
        <h2>公告中心</h2>
      </div>
      <div class="head-actions">
        <CompactHint tone="accent" title="发布公告" description="这里负责向全站普通用户推送系统公告。标题要短，正文要明确，跳转入口要真实可达。" />
        <el-button plain @click="loadAnnouncements">刷新公告</el-button>
        <RouterLink class="ghost-link" to="/ops">回后台总览</RouterLink>
      </div>
    </div>

    <PageStateBlock
      v-if="auth.isAuthenticated && !auth.user"
      tone="loading"
      title="正在确认管理员身份"
      description="稍等一下，正在确认当前账号权限。"
      compact
    />
    <PageStateBlock
      v-else-if="!isManagerUser"
      tone="error"
      title="当前账号没有发布公告权限"
      description="公告中心只对 manager 级后台账号开放。"
      action-label="回到首页"
      @action="router.push('/')"
    />
    <template v-else>
      <CollectionSkeleton v-if="loading && !announcements.length" variant="list" :card-count="4" />
      <RefreshFrame v-else :active="loading" label="正在同步公告中心">
        <div class="summary-grid">
          <article v-spotlight>
            <span>已发布公告</span>
            <strong>{{ announcements.length }}</strong>
            <p>这里只看最近 30 条公告。</p>
          </article>
          <article v-spotlight>
            <span>累计触达</span>
            <strong>{{ totalNotificationCount }}</strong>
            <p>所有已发布公告合计写入的站内提醒数。</p>
          </article>
          <article v-spotlight>
            <span>最近一条</span>
            <strong>{{ latestAnnouncementTitle }}</strong>
            <p>确认最近发布的是不是你想让用户先看到的内容。</p>
          </article>
        </div>

        <div class="admin-grid">
          <article class="card console-card" v-spotlight>
            <div class="card-head">
              <div>
                <h3>发布新公告</h3>
                <p>建议公告只讲一件事：发生了什么、用户该怎么做、需要去哪一步继续。</p>
              </div>
            </div>

            <el-form label-position="top" class="drawer-form">
              <el-form-item label="公告标题">
                <el-input v-model.trim="draft.title" maxlength="120" show-word-limit placeholder="例如：系统维护通知" />
              </el-form-item>
              <el-form-item label="公告正文">
                <el-input
                  v-model.trim="draft.body"
                  type="textarea"
                  :rows="5"
                  maxlength="255"
                  show-word-limit
                  placeholder="例如：今晚 23:00 到 23:30 将进行短时维护，期间部分报表生成会延迟。"
                />
              </el-form-item>
              <el-form-item label="点击跳转方式（可选）">
                <el-radio-group v-model="draft.link_mode">
                  <el-radio-button label="none">不跳转</el-radio-button>
                  <el-radio-button label="internal">站内页面</el-radio-button>
                  <el-radio-button label="external">站外网址</el-radio-button>
                </el-radio-group>
              </el-form-item>
              <el-form-item v-if="draft.link_mode === 'internal'" label="站内页面">
                <el-select v-model="draft.internal_link_path" style="width: 100%" placeholder="选择用户点开提醒后要去的前台页面">
                  <el-option v-for="item in internalLinkOptions" :key="item.value" :label="item.label" :value="item.value" />
                </el-select>
              </el-form-item>
              <el-form-item v-if="draft.link_mode === 'external'" label="站外网址">
                <el-input v-model.trim="draft.external_url" placeholder="例如：https://example.com/notice" />
              </el-form-item>
              <FormActionBar
                compact
                :tone="submitDisabled ? 'warning' : 'ready'"
                :title="submitDisabled ? '先补齐标题和正文' : '公告内容已完整，可以立即发布'"
                :description="formActionDescription"
                primary-label="发布公告"
                :disabled="submitDisabled"
                :loading="publishing"
                @primary="publishAnnouncement"
              />
            </el-form>
          </article>

          <article class="card console-card" v-spotlight>
            <div class="card-head">
              <div>
                <h3>最近公告</h3>
                <p>重点看标题是否清晰、触达人数是否合理，以及跳转页面是不是指向正确。</p>
              </div>
            </div>

            <div v-if="announcements.length" class="announcement-list">
              <article v-for="item in announcements" :key="item.id" class="announcement-item">
                <div class="announcement-head">
                  <div>
                    <strong>{{ item.title }}</strong>
                    <span>{{ formatDateTime(item.published_at) }} · {{ item.created_by?.display_name || item.created_by?.username || "管理员" }}</span>
                  </div>
                  <div class="announcement-head-actions">
                    <el-tag type="success" effect="light">已发布</el-tag>
                    <el-button text type="danger" :loading="deletingAnnouncementId === item.id" @click="removeAnnouncement(item)">删除公告</el-button>
                  </div>
                </div>
                <p>{{ item.body }}</p>
                <div class="announcement-meta">
                  <span>触达 {{ item.notification_count }} 人</span>
                  <span>{{ describeLink(item.link_path) }}</span>
                </div>
              </article>
            </div>
            <PageStateBlock
              v-else
              tone="empty"
              title="还没有发布过公告"
              description="发布第一条系统公告后，这里会开始沉淀历史记录。"
              compact
            />
          </article>
        </div>
      </RefreshFrame>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { RouterLink } from "vue-router";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import CompactHint from "../components/CompactHint.vue";
import FormActionBar from "../components/FormActionBar.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import { createAdminAnnouncement, deleteAdminAnnouncement, listAdminAnnouncements, type AdminAnnouncementItem } from "../api/adminAnnouncements";
import { extractApiErrorMessage, notifyActionSuccess, notifyErrorMessage, notifyLoadError } from "../lib/feedback";
import { isOpsManager } from "../lib/opsAccess";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();

const loading = ref(false);
const publishing = ref(false);
const deletingAnnouncementId = ref<number | null>(null);
const announcements = ref<AdminAnnouncementItem[]>([]);

const draft = reactive({
  title: "",
  body: "",
  link_mode: "none" as "none" | "internal" | "external",
  internal_link_path: "",
  external_url: "",
});

const isManagerUser = computed(() => isOpsManager(auth.user));
const internalLinkOptions = [
  { label: "首页", value: "/" },
  { label: "饮食记录", value: "/records" },
  { label: "菜谱库", value: "/recipes" },
  { label: "收藏", value: "/favorites" },
  { label: "目标", value: "/goals" },
  { label: "健康报表", value: "/reports" },
  { label: "社区", value: "/community" },
  { label: "个人档案", value: "/profile" },
  { label: "AI 助手", value: "/assistant" },
  { label: "会员中心", value: "/pricing" },
];
const resolvedLinkPath = computed(() => {
  if (draft.link_mode === "internal") {
    return draft.internal_link_path.trim();
  }
  if (draft.link_mode === "external") {
    return draft.external_url.trim();
  }
  return "";
});
const submitDisabled = computed(() => {
  if (!draft.title.trim() || !draft.body.trim()) {
    return true;
  }
  if (draft.link_mode === "internal") {
    return !draft.internal_link_path.trim();
  }
  if (draft.link_mode === "external") {
    return !draft.external_url.trim();
  }
  return false;
});
const totalNotificationCount = computed(() => announcements.value.reduce((sum, item) => sum + Number(item.notification_count || 0), 0));
const latestAnnouncementTitle = computed(() => announcements.value[0]?.title || "暂无");
const formActionDescription = computed(() => {
  if (draft.link_mode === "internal") {
    return draft.internal_link_path
      ? `用户点开提醒后会直接跳到站内页面：${draft.internal_link_path}`
      : "请选择一个站内页面，用户点开提醒后会直接进入该页面。";
  }
  if (draft.link_mode === "external") {
    return draft.external_url
      ? `用户点开提醒后会新开站外页面：${draft.external_url}`
      : "请输入完整站外网址，用户点开提醒后会新开外部页面。";
  }
  return "如果不设置跳转，用户点开公告后只会标记已读，不会离开当前页面。";
});

onMounted(() => {
  if (isManagerUser.value) {
    void loadAnnouncements();
  }
});

async function loadAnnouncements() {
  if (!isManagerUser.value) return;
  loading.value = true;
  try {
    const response = await listAdminAnnouncements();
    announcements.value = response.data?.items ?? [];
  } catch {
    notifyLoadError("公告中心");
  } finally {
    loading.value = false;
  }
}

function resetDraft() {
  draft.title = "";
  draft.body = "";
  draft.link_mode = "none";
  draft.internal_link_path = "";
  draft.external_url = "";
}

async function publishAnnouncement() {
  if (submitDisabled.value) {
    notifyErrorMessage("请先补齐公告标题、正文和对应跳转设置");
    return;
  }

  publishing.value = true;
  try {
    await createAdminAnnouncement({
      title: draft.title.trim(),
      body: draft.body.trim(),
      link_path: resolvedLinkPath.value,
    });
    notifyActionSuccess("公告已发布并写入站内提醒");
    resetDraft();
    await loadAnnouncements();
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "发布公告失败"));
  } finally {
    publishing.value = false;
  }
}

async function removeAnnouncement(item: AdminAnnouncementItem) {
  deletingAnnouncementId.value = item.id;
  try {
    await deleteAdminAnnouncement(item.id);
    notifyActionSuccess("公告已删除，并已从用户提醒中同步移除");
    await loadAnnouncements();
  } catch (error) {
    notifyErrorMessage(extractApiErrorMessage(error, "删除公告失败"));
  } finally {
    deletingAnnouncementId.value = null;
  }
}

function formatDateTime(value?: string) {
  if (!value) return "刚刚";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "刚刚";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function describeLink(linkPath?: string) {
  if (!linkPath) return "无跳转路径";
  if (/^https?:\/\//i.test(linkPath)) {
    return `站外：${linkPath}`;
  }
  return `站内：${linkPath}`;
}
</script>

<style scoped>
.admin-announcements {
  display: grid;
  gap: 18px;
}

.announcement-list {
  display: grid;
  gap: 12px;
}

.announcement-item {
  padding: 16px;
  border-radius: 18px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(247, 251, 255, 0.92);
}

.announcement-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.announcement-head-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.announcement-head strong {
  display: block;
  color: #173042;
}

.announcement-head span,
.announcement-meta span {
  color: #5a7a8a;
  font-size: 12px;
}

.announcement-item p {
  margin: 10px 0 0;
  color: #476072;
  line-height: 1.7;
}

.announcement-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 10px;
}

@media (max-width: 768px) {
  .announcement-head {
    flex-direction: column;
  }
}
</style>
