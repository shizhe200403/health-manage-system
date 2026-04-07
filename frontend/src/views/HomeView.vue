<template>
  <section class="dashboard">
    <CollectionSkeleton v-if="showDashboardSkeleton" variant="dashboard" :card-count="4" />
    <RefreshFrame v-else :active="loadingDashboard" label="正在更新首页数据">

      <!-- 顶部问候栏 -->
      <div class="greeting-bar">
        <div class="greeting-left">
          <h2 class="greeting-name">{{ greetingTitle }}</h2>
          <p class="greeting-sub">{{ todayProgressSummary }}</p>
        </div>
        <div class="greeting-right">
          <el-button type="primary" @click="goToNextMealRecord">{{ primaryRecordButtonLabel }}</el-button>
          <el-button plain @click="router.push('/favorites')">从收藏选餐</el-button>
          <el-button plain @click="openAssistantForTodayPlan">AI 建议</el-button>
        </div>
      </div>

      <!-- 双栏主体 -->
      <div class="main-layout">

        <!-- 左栏：状态聚合 -->
        <aside class="sidebar">

          <!-- 今日状态卡 -->
          <div class="sidebar-card status-card" :class="{ 'is-refresh-pulse': dashboardRefreshPulse }">
            <div class="sidebar-card-header">
              <span class="card-label">今日状态</span>
              <span class="status-badge" :class="hasTodayRecord ? 'badge-active' : 'badge-muted'">
                {{ heroStatusHeadline }}
              </span>
            </div>

            <!-- 营养进度 -->
            <div class="nutrition-rows">
              <div v-for="item in focusMetricCards" :key="item.key" class="nutrition-row" :class="`tone-${item.tone}`">
                <div class="nutrition-row-head">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.value }}</strong>
                  <em class="nutrition-badge">{{ item.badge }}</em>
                </div>
                <div class="nutrition-bar-track">
                  <div
                    class="nutrition-bar-fill"
                    :style="{
                      width: item.tone === 'success' ? '100%'
                        : item.tone === 'steady' ? '70%'
                        : item.tone === 'warning' ? '40%'
                        : '10%'
                    }"
                  />
                </div>
                <p class="nutrition-copy">{{ item.copy }}</p>
              </div>
            </div>

            <!-- 四餐打卡 -->
            <div class="meal-checklist">
              <div
                v-for="item in todayMealChecklist"
                :key="item.value"
                class="meal-check-item"
                :class="{ done: item.done, focus: item.value === nextMealFocusType }"
              >
                <span class="meal-dot" />
                <span class="meal-label">{{ item.label }}</span>
                <span class="meal-status">{{ item.done ? "✓" : item.value === nextMealFocusType ? "优先" : "—" }}</span>
              </div>
            </div>
          </div>

          <!-- 目标卡 -->
          <div class="sidebar-card goal-card">
            <div class="sidebar-card-header">
              <span class="card-label">当前目标</span>
              <el-button text size="small" @click="router.push('/goals')">查看</el-button>
            </div>
            <template v-if="activeGoal">
              <strong class="goal-name">{{ goalTypeLabel(activeGoal.goal_type) }}</strong>
              <p class="goal-desc">{{ activeGoal.description || "继续推进中" }}</p>
              <div class="goal-progress-row">
                <span>{{ formatDecimal(activeGoal.current_value) }}</span>
                <span>/ {{ formatDecimal(activeGoal.target_value) }}</span>
                <span class="focus-badge goal-progress-badge">{{ goalProgressLabel }}</span>
              </div>
              <el-progress :percentage="goalProgressPercent" :stroke-width="8" :show-text="false" />
            </template>
            <p v-else class="goal-empty">还没有进行中的目标，<el-button text @click="router.push('/goals')">去创建</el-button></p>
          </div>

          <!-- 快捷操作 -->
          <div class="sidebar-card quick-actions-card">
            <span class="card-label">快捷操作</span>
            <div class="quick-btn-list">
              <el-button class="quick-btn" @click="goToNextMealRecord">{{ primaryRecordButtonLabel }}</el-button>
              <el-button class="quick-btn" plain @click="router.push('/favorites')">去收藏中心</el-button>
              <el-button class="quick-btn" plain @click="router.push('/recipes')">浏览菜谱库</el-button>
              <el-button class="quick-btn" plain @click="router.push('/records')">查看记录</el-button>
            </div>
          </div>

          <!-- 起步引导（仅在需要时显示） -->
          <div v-if="onboardingSteps.length" class="sidebar-card onboarding-card">
            <span class="card-label">起步引导</span>
            <div class="onboarding-steps">
              <div v-for="item in onboardingSteps" :key="item.title" class="onboarding-step">
                <div>
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.copy }}</p>
                </div>
                <el-button size="small" plain @click="router.push(item.to)">{{ item.cta }}</el-button>
              </div>
            </div>
          </div>
        </aside>

        <!-- 右栏：主工作区 -->
        <main class="main-content">

          <!-- 工作台标题区 -->
          <div class="workbench-header">
            <div class="workbench-headline">
              <span class="workbench-kicker">Today Flow</span>
              <strong>{{ todayWorkbenchHeadline }}</strong>
              <p>{{ todayWorkbenchDescription }}</p>
            </div>
            <div class="workbench-actions">
              <el-button v-if="todaySuggestedRecipe" plain @click="addToRecord(todaySuggestedRecipe)">一键带入推荐菜</el-button>
              <el-button plain @click="openAssistantForTodayPlan">AI 解释下一步</el-button>
            </div>
          </div>

          <!-- 四餐进度横排 -->
          <div class="meal-progress-row">
            <article
              v-for="item in todayMealChecklist"
              :key="item.value"
              v-spotlight
              class="meal-progress-card"
              :class="{ done: item.done, active: item.value === nextMealFocusType }"
              @click="goToNextMealRecord"
            >
              <span class="meal-card-label">{{ item.label }}</span>
              <strong>{{ item.done ? "已记录" : item.value === nextMealFocusType ? "建议优先" : "待补" }}</strong>
              <p>{{ item.done ? "今天这餐已落下记录" : `下一步可先补${item.label}` }}</p>
            </article>
          </div>

          <!-- 推荐菜谱横排 -->
          <div class="section-block">
            <div class="section-block-header">
              <h3>推荐菜谱</h3>
              <div class="section-block-actions">
                <el-button text @click="loadDashboard">刷新</el-button>
                <el-button text @click="router.push('/recipes')">去菜谱库</el-button>
              </div>
            </div>
            <div v-if="recommendations.length" class="recommend-row">
              <article v-for="item in featuredRecommendations" :key="item.recipe_id" v-spotlight class="recommend-card-h">
                <strong>{{ item.title }}</strong>
                <p>{{ item.reason_text }}</p>
                <div class="recommend-card-actions">
                  <el-button text size="small" @click="openRecipeDetail(item)">查看详情</el-button>
                  <el-button text size="small" @click="showReason(item.recipe_id)">推荐原因</el-button>
                </div>
              </article>
            </div>
            <PageStateBlock
              v-else
              tone="empty"
              title="当前还没有可展示的推荐"
              description="把健康档案补一补，再记几餐，推荐就会越来越懂你。"
              action-label="去完善资料"
              compact
              @action="router.push('/profile')"
            />
          </div>

          <!-- 下一餐推荐 + 延展工作区 -->
          <div class="lower-grid">
            <!-- 下一餐推荐 -->
            <div class="next-meal-card" v-spotlight>
              <span class="card-label">下一餐更省事</span>
              <strong>{{ todaySuggestedRecipe?.title || "先去挑一顿合适的菜" }}</strong>
              <p>{{ todaySuggestedRecipeCopy }}</p>
              <div class="next-meal-actions">
                <el-button v-if="todaySuggestedRecipe" text @click="openFavoriteDetail(todaySuggestedRecipe)">查看详情</el-button>
                <el-button v-if="todaySuggestedRecipe" type="primary" plain size="small" @click="addToRecord(todaySuggestedRecipe)">加入记录</el-button>
                <el-button v-else plain @click="router.push('/recipes')">去菜谱库</el-button>
              </div>
            </div>

            <!-- 延展工作区 -->
            <div class="extension-panel">
              <div class="extension-tab-strip" role="tablist">
                <button
                  v-for="item in extensionTabs"
                  :key="item.key"
                  class="extension-tab"
                  :class="{ active: extensionTab === item.key }"
                  type="button"
                  role="tab"
                  @click="setExtensionTab(item.key)"
                >
                  <span>{{ item.label }}</span>
                  <strong>{{ item.status }}</strong>
                </button>
              </div>

              <div class="extension-body">
                <div v-if="extensionTab === 'favorites'" class="shortcut-list">
                  <article v-for="item in favoriteShortcuts" :key="item.id" v-spotlight class="shortcut-item interactive-shortcut-item">
                    <div>
                      <strong>{{ item.title }}</strong>
                      <p>{{ item.description || "已收藏，可直接加入记录。" }}</p>
                    </div>
                    <div class="shortcut-actions">
                      <el-button text @click="openFavoriteDetail(item)">详情</el-button>
                      <el-button type="primary" plain size="small" @click="addToRecord(item)">加入记录</el-button>
                    </div>
                  </article>
                  <PageStateBlock v-if="!favoriteShortcuts.length" tone="empty" title="还没有收藏" description="遇到合适的菜谱先收藏，后续记录会快很多。" action-label="去菜谱库" compact @action="router.push('/recipes')" />
                </div>

                <div v-else-if="extensionTab === 'records'" class="record-list">
                  <article v-for="record in recentRecords.slice(0, 4)" :key="record.id" v-spotlight class="record-item interactive-record-item">
                    <div>
                      <strong>{{ record.record_date }} · {{ mealTypeLabel(record.meal_type) }}</strong>
                      <p>{{ record.items?.[0]?.recipe_title || record.note || "已记录一餐" }}</p>
                    </div>
                    <span>{{ record.items?.length || 0 }} 条目</span>
                  </article>
                  <PageStateBlock v-if="!recentRecords.length" tone="empty" title="最近还没有记录" description="先记一餐，趋势和推荐就有素材了。" action-label="去记录" compact @action="router.push('/records')" />
                </div>

                <div v-else-if="extensionTab === 'trend'">
                  <TrendMiniBars v-if="weekEnergyBars.length" title="最近7天热量节奏" description="看一眼最近几天的整体摄入强弱，判断今天是不是明显偏高或偏低。" badge="近7天" tone="energy" compact :items="weekEnergyBars" />
                  <PageStateBlock v-else tone="empty" title="最近还没有趋势数据" description="先记录几餐，热量节奏才会出现。" compact />
                </div>

                <div v-else-if="extensionTab === 'goals'">
                  <div v-if="activeGoal" class="focus-box">
                    <div class="focus-topline">
                      <strong>{{ goalTypeLabel(activeGoal.goal_type) }}</strong>
                      <span class="focus-badge">{{ goalProgressLabel }}</span>
                    </div>
                    <p>{{ activeGoal.description || "已创建目标，建议继续补录进展。" }}</p>
                    <div class="progress-line">
                      <span>当前 {{ formatDecimal(activeGoal.current_value) }}</span>
                      <span>目标 {{ formatDecimal(activeGoal.target_value) }}</span>
                    </div>
                    <el-progress :percentage="goalProgressPercent" :stroke-width="8" :show-text="false" />
                  </div>
                  <PageStateBlock v-else tone="empty" title="你还没有正在进行的目标" description="先创建一个最明确的健康目标。" action-label="去创建目标" compact @action="router.push('/goals')" />
                </div>

                <div v-else>
                  <div v-if="latestReport" class="focus-box">
                    <strong>{{ reportTypeLabel(latestReport.report_type) }} · {{ reportStatusLabel(latestReport.status) }}</strong>
                    <p>{{ formatDateRange(latestReport.start_date, latestReport.end_date) }}</p>
                    <a v-if="latestReport.file_url" :href="latestReport.file_url" target="_blank" rel="noreferrer">打开最新报表</a>
                  </div>
                  <PageStateBlock v-else tone="empty" title="还没有生成过报表" description="当记录累计起来后，再做周报和月报才有复盘价值。" action-label="去报表页" compact @action="router.push('/reports')" />
                </div>
              </div>
            </div>
          </div>

        </main>
      </div>

      <RecipeDetailDialog
        v-model="detailVisible"
        :recipe-id="selectedRecipeId"
        :recipe="selectedRecipe"
        :favorited="selectedRecipeId ? favoriteIds.includes(selectedRecipeId) : false"
        :reason-text="selectedReasonText"
        @favorite-change="handleFavoriteChange"
        @add-to-record="addToRecord"
      />
    </RefreshFrame>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import CollectionSkeleton from "../components/CollectionSkeleton.vue";
import PageStateBlock from "../components/PageStateBlock.vue";
import RefreshFrame from "../components/RefreshFrame.vue";
import TrendMiniBars from "../components/TrendMiniBars.vue";
import { ElMessageBox, notifyLoadError } from "../lib/feedback";
import { useRouter } from "vue-router";
import RecipeDetailDialog from "../components/RecipeDetailDialog.vue";
import { useAuthStore } from "../stores/auth";
import { explainRecommendation, listFavoriteRecipes, listRecommendations, profileRecommendations } from "../api/recipes";
import { getMe } from "../api/auth";
import { trackEvent } from "../api/behavior";
import { nutritionAnalysis } from "../api/nutrition";
import { listMealRecords, mealStatistics } from "../api/tracking";
import { listHealthGoals } from "../api/goals";
import { listReportTasks } from "../api/reports";
import { useAnimatedNumber } from "../composables/useAnimatedNumber";

const router = useRouter();
const auth = useAuthStore();
const loadingDashboard = ref(true);
const dashboardReady = ref(false);
const recommendations = ref<Array<{ recipe_id: number; title: string; reason_text: string }>>([]);
const favoriteIds = ref<number[]>([]);
const favoriteItems = ref<any[]>([]);
const favoriteCount = ref(0);
const recentRecords = ref<any[]>([]);
const goals = ref<any[]>([]);
const reportTasks = ref<any[]>([]);
const dashboardRefreshPulse = ref(false);
let dashboardPulseTimer: ReturnType<typeof window.setTimeout> | null = null;
const weekTrend = ref<Array<Record<string, any>>>([]);
const todayMetrics = reactive({
  energy: 0,
  protein: 0,
  fat: 0,
  carbohydrate: 0,
});
const nutritionSummary = reactive({
  bmi: "-",
  goal_hint: "",
  calorie_target: "-",
  protein_target: "-",
});
const detailVisible = ref(false);
const selectedRecipeId = ref<number | null>(null);
const selectedRecipe = ref<Record<string, any> | null>(null);
const selectedReasonText = ref("");
const showDashboardSkeleton = computed(() => loadingDashboard.value && !dashboardReady.value);
type ExtensionTabKey = "favorites" | "records" | "trend" | "goals" | "reports";
const extensionTab = ref<ExtensionTabKey>("records");
const extensionTabTouched = ref(false);

const profileReady = computed(() => {
  const profile = auth.user?.profile;
  return Boolean(profile?.height_cm && profile?.weight_kg && profile?.target_weight_kg);
});
const greetingTitle = computed(() => {
  const name = auth.user?.nickname || auth.user?.username || "你";
  return `${name}，吃对每一餐，健康每一天`;
});
const activeGoal = computed(() => goals.value.find((item) => item.status === "active") ?? null);
const latestReport = computed(() => reportTasks.value[0] ?? null);
const favoriteShortcuts = computed(() => favoriteItems.value.slice(0, 3));
const featuredRecommendations = computed(() => recommendations.value.slice(0, 3));
const hasTodayRecord = computed(() => recentRecords.value.some((item) => item.record_date === todayString()));
const todayRecordSet = computed(() => new Set(recentRecords.value.filter((item) => item.record_date === todayString()).map((item) => item.meal_type)));
const todayMealChecklist = computed(() => [
  { label: "早餐", value: "breakfast", done: todayRecordSet.value.has("breakfast") },
  { label: "午餐", value: "lunch", done: todayRecordSet.value.has("lunch") },
  { label: "晚餐", value: "dinner", done: todayRecordSet.value.has("dinner") },
  { label: "加餐", value: "snack", done: todayRecordSet.value.has("snack") },
]);
const todayCompletedMealCount = computed(() => todayMealChecklist.value.filter((item) => item.done).length);
const animatedTodayCompletedMealCount = useAnimatedNumber(todayCompletedMealCount);
const nextMealFocusType = computed<"breakfast" | "lunch" | "dinner" | "snack">(() => {
  const anchor = currentMealType();
  if (!todayRecordSet.value.has(anchor)) {
    return anchor;
  }
  return (
    ["breakfast", "lunch", "dinner", "snack"].find((mealType) => !todayRecordSet.value.has(mealType)) || "snack"
  ) as "breakfast" | "lunch" | "dinner" | "snack";
});
const calorieTargetNumber = computed(() => Number(nutritionSummary.calorie_target) || 0);
const proteinTargetNumber = computed(() => Number(nutritionSummary.protein_target) || 0);
const energyGap = computed(() => Math.max(0, calorieTargetNumber.value - todayMetrics.energy));
const proteinGap = computed(() => Math.max(0, proteinTargetNumber.value - todayMetrics.protein));
const weekRecordedDays = computed(() => weekTrend.value.slice(-7).filter((item) => Number(item.energy || 0) > 0).length);
const animatedTodayEnergy = useAnimatedNumber(computed(() => Number(todayMetrics.energy || 0)), { duration: 520, decimals: 1 });
const animatedTodayProtein = useAnimatedNumber(computed(() => Number(todayMetrics.protein || 0)), { duration: 520, decimals: 1 });
const animatedTodayFat = useAnimatedNumber(computed(() => Number(todayMetrics.fat || 0)), { duration: 520, decimals: 1 });
const animatedTodayCarbohydrate = useAnimatedNumber(computed(() => Number(todayMetrics.carbohydrate || 0)), { duration: 520, decimals: 1 });
const weekAverageEnergy = computed(() => {
  const activeDays = weekTrend.value
    .slice(-7)
    .map((item) => Number(item.energy || 0))
    .filter((value) => value > 0);
  if (!activeDays.length) {
    return 0;
  }
  return activeDays.reduce((sum, value) => sum + value, 0) / activeDays.length;
});
const latestReportAgeDays = computed(() => {
  const generatedAt = latestReport.value?.generated_at;
  if (!generatedAt) {
    return null;
  }
  const diff = Date.now() - new Date(generatedAt).getTime();
  if (!Number.isFinite(diff) || diff < 0) {
    return null;
  }
  return Math.floor(diff / (1000 * 60 * 60 * 24));
});
const todayMetricCards = computed(() => {
  const items = [
    {
      key: "energy",
      label: "热量",
      value: formatMetric(animatedTodayEnergy.value, "kcal"),
      target: Number(nutritionSummary.calorie_target) || 0,
    },
    {
      key: "protein",
      label: "蛋白质",
      value: formatMetric(animatedTodayProtein.value, "g"),
      target: Number(nutritionSummary.protein_target) || 0,
    },
    {
      key: "fat",
      label: "脂肪",
      value: formatMetric(animatedTodayFat.value, "g"),
      target: 0,
    },
    {
      key: "carbohydrate",
      label: "碳水",
      value: formatMetric(animatedTodayCarbohydrate.value, "g"),
      target: 0,
    },
  ];

  return items.map((item) => {
    const actual = Number(todayMetrics[item.key as keyof typeof todayMetrics]) || 0;
    if (item.target > 0) {
      const ratio = actual / item.target;
      return {
        ...item,
        badge: ratio >= 1 ? "已达标" : ratio >= 0.7 ? "接近目标" : "仍有缺口",
        tone: ratio >= 1 ? "success" : ratio >= 0.7 ? "steady" : "warning",
        copy: ratio >= 1 ? `已达到今日目标 ${formatMetric(item.target, item.key === "energy" ? "kcal" : "g")}` : `目标 ${formatMetric(item.target, item.key === "energy" ? "kcal" : "g")}`,
      };
    }
    return {
      ...item,
      badge: actual > 0 ? "已记录" : "暂无",
      tone: actual > 0 ? "steady" : "muted",
      copy: actual > 0 ? "今日已有摄入记录" : "今天还没有相关摄入数据",
    };
  });
});
const focusMetricCards = computed(() => todayMetricCards.value.slice(0, 2));
const heroNextActions = computed(() => nextActions.value.slice(0, 3));
const heroStatusHeadline = computed(() => {
  if (!hasTodayRecord.value) {
    return "今天还没开始推进";
  }
  if (todayMealChecklist.value.every((item) => item.done)) {
    return "四餐节奏已经补齐";
  }
  return `已推进 ${todayCompletedMealCount.value} / 4 餐`;
});
const todaySuggestedRecipe = computed<Record<string, any> | null>(() => {
  const favoriteMatch = favoriteItems.value.find((item) => item.meal_type === nextMealFocusType.value) ?? favoriteItems.value[0];
  if (favoriteMatch) {
    return favoriteMatch;
  }
  const recommendationMatch = recommendations.value.find((item) => item.meal_type === nextMealFocusType.value) ?? recommendations.value[0];
  if (!recommendationMatch) {
    return null;
  }
  return {
    id: recommendationMatch.recipe_id,
    title: recommendationMatch.title,
    description: recommendationMatch.reason_text,
    meal_type: recommendationMatch.meal_type || nextMealFocusType.value,
  };
});
const primaryRecordButtonLabel = computed(() => `去记${mealTypeLabel(nextMealFocusType.value)}`);
const todayProgressSummary = computed(() => {
  if (!hasTodayRecord.value) {
    return "今天还没有任何记录，先把第一餐记上，缺口和建议才能真正帮到你。";
  }
  if (proteinTargetNumber.value > 0 && proteinGap.value >= 18) {
    return `今天蛋白质还差约 ${formatMetric(proteinGap.value, "g")}，下一餐更适合优先补高蛋白。`;
  }
  if (calorieTargetNumber.value > 0 && todayMetrics.energy > calorieTargetNumber.value * 1.15) {
    return "今天热量已经明显偏高，后续一餐更适合轻负担一点。";
  }
  if (calorieTargetNumber.value > 0 && energyGap.value > 0) {
    return `距离今日热量目标还差约 ${formatMetric(energyGap.value, "kcal")}，可以继续补一餐或补记录。`;
  }
  return "今天主要指标已经接近目标，可以把注意力放到记录连续性和下一餐质量。";
});
const todayWorkbenchHeadline = computed(() => {
  if (!hasTodayRecord.value) {
    return "先把今天第一餐记上";
  }
  if (todayMealChecklist.value.every((item) => item.done)) {
    return "今天的主线已经基本齐了";
  }
  if (proteinTargetNumber.value > 0 && proteinGap.value >= 18) {
    return `先补${mealTypeLabel(nextMealFocusType.value)}，顺手把蛋白缺口拉上来`;
  }
  return `现在最值得先补${mealTypeLabel(nextMealFocusType.value)}`;
});
const todayWorkbenchDescription = computed(() => {
  if (!hasTodayRecord.value) {
    return "先记一餐，今天的缺口、推荐和复盘建议才会真正开始运转。";
  }
  if (todayMealChecklist.value.every((item) => item.done)) {
    return "如果只是补录，优先去记录页复用上一餐；如果今天已经记全，就回看趋势和报表。";
  }
  if (proteinTargetNumber.value > 0 && proteinGap.value >= 18) {
    return `今天蛋白还差约 ${formatMetric(proteinGap.value, "g")}，下一餐优先补高蛋白会比继续观望更有效。`;
  }
  if (calorieTargetNumber.value > 0 && energyGap.value > 0) {
    return `距离今日热量目标还差约 ${formatMetric(energyGap.value, "kcal")}，现在直接补上下一餐最省事。`;
  }
  return `当前最自然的动作是先补${mealTypeLabel(nextMealFocusType.value)}，别让今天断在半路。`;
});
const todaySuggestedRecipeCopy = computed(() => {
  if (!todaySuggestedRecipe.value) {
    return "如果收藏和推荐还不够，就直接去菜谱库按当前时段挑一顿更合适的。";
  }
  if (favoriteIds.value.includes(Number(todaySuggestedRecipe.value.id))) {
    return "这道菜已经进过你的收藏，直接带入记录会更快。";
  }
  if (todaySuggestedRecipe.value.meal_type === nextMealFocusType.value) {
    return `它更贴近当前该补的${mealTypeLabel(nextMealFocusType.value)}，可以直接一键带入记录。`;
  }
  return todaySuggestedRecipe.value.description || "这是当前更值得先看的下一餐候选。";
});
const weekEnergyBars = computed(() => {
  return weekTrend.value.slice(-7).map((item, index, source) => ({
    label: String(item.date || "").slice(5),
    value: Number(item.energy || 0),
    display: `${Number(item.energy || 0).toFixed(0)}`,
    highlight: index === source.length - 1,
  }));
});
const goalProgressPercent = computed(() => {
  const goal = activeGoal.value;
  if (!goal) {
    return 0;
  }
  const target = Number(goal.target_value || 0);
  const current = Number(goal.current_value || 0);
  if (!target) {
    return 0;
  }
  return Math.max(0, Math.min(100, Math.round((current / target) * 100)));
});
const goalProgressLabel = computed(() => {
  if (!activeGoal.value) {
    return "";
  }
  if (goalProgressPercent.value >= 100) {
    return "已达成";
  }
  if (goalProgressPercent.value >= 70) {
    return "推进顺畅";
  }
  return "继续推进";
});
const suggestedExtensionTab = computed<ExtensionTabKey>(() => {
  if (!hasTodayRecord.value) {
    return "records";
  }
  if (favoriteShortcuts.value.length) {
    return "favorites";
  }
  if (activeGoal.value) {
    return "goals";
  }
  if (weekEnergyBars.value.length) {
    return "trend";
  }
  if (latestReport.value) {
    return "reports";
  }
  return "records";
});
const extensionTabs = computed(() => [
  {
    key: "favorites" as ExtensionTabKey,
    label: "收藏捷径",
    status: favoriteShortcuts.value.length ? `${favoriteShortcuts.value.length} 个可复用` : "待沉淀",
  },
  {
    key: "records" as ExtensionTabKey,
    label: "最近记录",
    status: recentRecords.value.length ? `${Math.min(recentRecords.value.length, 4)} 条最近记录` : "暂无记录",
  },
  {
    key: "trend" as ExtensionTabKey,
    label: "本周节奏",
    status: weekRecordedDays.value ? `${weekRecordedDays.value} 天已记录` : "暂无趋势",
  },
  {
    key: "goals" as ExtensionTabKey,
    label: "当前目标",
    status: activeGoal.value ? goalTypeLabel(activeGoal.value.goal_type) : "待建立",
  },
  {
    key: "reports" as ExtensionTabKey,
    label: "最新报表",
    status: latestReport.value ? reportTypeLabel(latestReport.value.report_type) : "未生成",
  },
]);
const activeExtensionMeta = computed(() => {
  if (extensionTab.value === "favorites") {
    return {
      kicker: "Reusable Picks",
      title: favoriteShortcuts.value.length ? "把已经验证过的选择变成下一餐入口" : "先开始沉淀常用菜谱",
      copy: favoriteShortcuts.value.length
        ? "收藏页最有价值的不是囤积，而是把下一次决策变短。这里直接回到你最容易复用的几道菜。"
        : "当收藏开始积累，首页和记录页都会明显顺手很多，尤其是赶时间的时候。",
      cta: favoriteShortcuts.value.length ? "去收藏中心" : "去菜谱库",
      to: favoriteShortcuts.value.length ? "/favorites" : "/recipes",
    };
  }
  if (extensionTab.value === "records") {
    return {
      kicker: "Recent Log",
      title: recentRecords.value.length ? "先看你最近怎么吃，再决定今天要不要补" : "先记下一餐，一切就跑起来了",
      copy: recentRecords.value.length
        ? "最近记录放在这里，不必反复翻整页记录，也更容易判断今天是漏记还是重复。"
        : "没有真实记录时，推荐、趋势和报表都只能停在半空，先把第一餐记上最划算。",
      cta: "去记录页",
      to: "/records",
    };
  }
  if (extensionTab.value === "trend") {
    return {
      kicker: "Week Rhythm",
      title: weekEnergyBars.value.length ? "把今天放回最近一周里看" : "先补够几天记录，再谈趋势",
      copy: weekEnergyBars.value.length
        ? "今天偏高还是偏低，不该只看单日。先看最近 7 天的节奏，再决定要不要收一收或补一补。"
        : "趋势模块的价值在于连续性，没有几天真实输入时，结论只会失真。",
      cta: "去记录页",
      to: "/records",
    };
  }
  if (extensionTab.value === "goals") {
    return {
      kicker: "Goal Focus",
      title: activeGoal.value ? "首页只盯住一个正在推进的目标" : "先给系统一个明确方向",
      copy: activeGoal.value
        ? "目标不该只是设置一次就放着，最好能持续作为今天饮食选择的判断准绳。"
        : "没有明确目标时，推荐、记录和报表很容易变成零散信息，先把主目标定下来。",
      cta: "去目标页",
      to: "/goals",
    };
  }
  return {
    kicker: "Review Loop",
    title: latestReport.value ? "把记录变成复盘，而不只是积累数据" : "等基础记录起来后，再开始阶段复盘",
    copy: latestReport.value
      ? "报表的作用不是展示数字，而是帮你判断这周到底做得怎么样，以及下一步该改什么。"
      : "先把几天记录走通，等有足够输入之后再生成周报，复盘结论才会有意义。",
    cta: "去报表页",
    to: "/reports",
  };
});
const nextActions = computed(() => {
  const actions: Array<{ title: string; copy: string; cta: string; to: string }> = [];
  const registerAction = (title: string, copy: string, cta: string, to: string) => {
    if (actions.some((item) => item.title === title)) {
      return;
    }
    actions.push({ title, copy, cta, to });
  };

  if (!profileReady.value) {
    registerAction("先补齐健康档案", "身高、体重和目标体重是推荐和目标计算的基础。", "去完善", "/profile");
  }
  if (!activeGoal.value) {
    registerAction("建立一个重点目标", "有了明确目标，推荐、记录和报表会更贴近你当前的需要。", "去创建", "/goals");
  }
  if (!hasTodayRecord.value) {
    registerAction("补上今天第一条记录", "记一餐，今天的摄入和缺口就看得见了。", "去记录", "/records");
  }
  if (hasTodayRecord.value && proteinTargetNumber.value > 0 && proteinGap.value >= 18) {
    registerAction(
      "今天蛋白质还有明显缺口",
      `距离今日目标还差约 ${formatMetric(proteinGap.value, "g")}，优先补一份高蛋白菜谱更有效。`,
      favoriteCount.value ? "去收藏中心" : "去找菜谱",
      favoriteCount.value ? "/favorites" : "/recipes",
    );
  }
  if (hasTodayRecord.value && calorieTargetNumber.value > 0 && todayMetrics.energy > calorieTargetNumber.value * 1.15) {
    registerAction(
      "今天热量已经偏高",
      "后续一餐更适合选择轻负担、低油低糖的搭配，避免继续上冲。",
      "看菜谱建议",
      "/recipes",
    );
  }
  if (hasTodayRecord.value && calorieTargetNumber.value > 0 && todayMetrics.energy > 0 && todayMetrics.energy < calorieTargetNumber.value * 0.55) {
    registerAction(
      "今天热量还偏低",
      `当前距离目标还差约 ${formatMetric(energyGap.value, "kcal")}，如果还有一餐未记，先补记录。`,
      "继续补记录",
      "/records",
    );
  }
  if (weekRecordedDays.value > 0 && weekRecordedDays.value < 4) {
    registerAction("这一周记录连续性偏弱", "最近 7 天活跃天数还不够，先把记录连续性补起来，再看趋势和报表。", "去补记录", "/records");
  }
  if (weekRecordedDays.value >= 4 && (!latestReport.value || (latestReportAgeDays.value ?? 999) >= 7)) {
    registerAction(
      "可以安排一次阶段复盘",
      "最近一周已经有基本记录覆盖，适合生成新周报，把输入变成复盘结果。",
      "去报表页",
      "/reports",
    );
  }
  if (weekAverageEnergy.value > 0 && calorieTargetNumber.value > 0 && weekAverageEnergy.value > calorieTargetNumber.value * 1.1) {
    registerAction(
      "最近一周整体摄入偏高",
      "过去几天的平均热量已经持续高于目标，建议从收藏或菜谱里替换掉一两道高负担选择。",
      favoriteCount.value ? "去收藏中心" : "去菜谱库",
      favoriteCount.value ? "/favorites" : "/recipes",
    );
  }
  if (!favoriteCount.value) {
    registerAction("沉淀几个可复用菜谱", "收藏越完整，后续记录和决策成本越低。", "去挑选", "/recipes");
  }
  return actions.slice(0, 4);
});
const onboardingSteps = computed(() => {
  const steps = [];
  if (!profileReady.value) {
    steps.push({
      title: "完善档案",
      copy: "先补齐身高、体重和目标体重，后续推荐与目标才不会漂。",
      cta: "去完善",
      to: "/profile",
    });
  }
  if (!recentRecords.value.length) {
    steps.push({
      title: "记录第一餐",
      copy: "先形成一条真实饮食记录，首页、统计和报表才会开始动起来。",
      cta: "去记录",
      to: "/records",
    });
  }
  if (!favoriteCount.value) {
    steps.push({
      title: "收藏常用菜谱",
      copy: "把可复用选择沉淀下来，之后每天记录会更顺手。",
      cta: "去收藏",
      to: "/recipes",
    });
  }
  if (!latestReport.value && recentRecords.value.length) {
    steps.push({
      title: "生成第一份周报",
      copy: "有了基础记录后，生成一份周报会更容易看清这一周的变化。",
      cta: "去报表",
      to: "/reports",
    });
  }
  return steps.slice(0, 4);
});

watch(
  suggestedExtensionTab,
  (value) => {
    if (!extensionTabTouched.value) {
      extensionTab.value = value;
    }
  },
  { immediate: true },
);

function todayString() {
  const date = new Date();
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function currentMealType(): "breakfast" | "lunch" | "dinner" | "snack" {
  const hour = new Date().getHours();
  if (hour < 10) {
    return "breakfast";
  }
  if (hour < 15) {
    return "lunch";
  }
  if (hour < 20) {
    return "dinner";
  }
  return "snack";
}

function formatMetric(value: unknown, unit: string) {
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) {
    return `0 ${unit}`;
  }
  return `${number.toFixed(unit === "kcal" ? 0 : 1)} ${unit}`;
}

function formatDecimal(value: unknown) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "-";
  }
  return number.toFixed(1);
}

function goalTypeLabel(value: string) {
  return {
    weight_loss: "减重",
    muscle_gain: "增肌",
    blood_sugar_control: "控糖",
    fat_control: "控脂",
    protein_up: "提升蛋白摄入",
    diet_balance: "饮食均衡",
  }[value] || value;
}

function mealTypeLabel(value: string) {
  return {
    breakfast: "早餐",
    lunch: "午餐",
    dinner: "晚餐",
    snack: "加餐",
  }[value] || value;
}

function reportTypeLabel(type: string) {
  return type === "monthly" ? "月报" : "周报";
}

function reportStatusLabel(status: string) {
  return {
    pending: "等待中",
    processing: "生成中",
    completed: "已完成",
    failed: "失败",
  }[status] || status;
}

function formatDateRange(startDate?: string, endDate?: string) {
  if (!startDate && !endDate) {
    return "未记录";
  }
  return `${startDate || "-"} 至 ${endDate || "-"}`;
}

function unwrapPayload<T>(payload: unknown, fallback: T): T {
  if (payload == null) {
    return fallback;
  }
  if (typeof payload === "object" && payload && "data" in payload && (payload as { data?: T }).data !== undefined) {
    return (payload as { data: T }).data;
  }
  return payload as T;
}

function unwrapList(payload: unknown) {
  const raw = unwrapPayload<any>(payload, []);
  if (Array.isArray(raw)) {
    return raw;
  }
  if (Array.isArray(raw?.items)) {
    return raw.items;
  }
  if (Array.isArray(raw?.results)) {
    return raw.results;
  }
  return [];
}

async function loadDashboard() {
  try {
    loadingDashboard.value = true;
    const [meResult, recommendationResult, nutritionResult, favoriteResult, goalResult, reportResult, statsResult, recordsResult] =
      await Promise.allSettled([
        getMe(),
        listRecommendations(),
        nutritionAnalysis(),
        listFavoriteRecipes(),
        listHealthGoals(),
        listReportTasks(),
        mealStatistics("week"),
        listMealRecords(),
      ]);

    const meResponse = meResult.status === "fulfilled" ? meResult.value : null;
    const recommendationResponse = recommendationResult.status === "fulfilled" ? recommendationResult.value : null;
    const nutritionResponse = nutritionResult.status === "fulfilled" ? nutritionResult.value : null;
    const favoriteResponse = favoriteResult.status === "fulfilled" ? favoriteResult.value : null;
    const goalResponse = goalResult.status === "fulfilled" ? goalResult.value : null;
    const reportResponse = reportResult.status === "fulfilled" ? reportResult.value : null;
    const statsResponse = statsResult.status === "fulfilled" ? statsResult.value : null;
    const recordsResponse = recordsResult.status === "fulfilled" ? recordsResult.value : null;

    if (!meResponse && !recommendationResponse && !nutritionResponse) {
      throw new Error("dashboard load failed");
    }

    const meData = unwrapPayload<Record<string, any> | null>(meResponse, null);
    const nutritionData = unwrapPayload<Record<string, any>>(nutritionResponse, {});
    const recommendationData = unwrapList(recommendationResponse);
    // 若 home 推荐为空，尝试 by-profile 推荐作为 fallback
    let finalRecommendationData = recommendationData;
    if (!recommendationData.length) {
      try {
        const profileResult = await profileRecommendations();
        finalRecommendationData = unwrapList(profileResult);
      } catch {
        // ignore
      }
    }
    const favoriteData = unwrapList(favoriteResponse);
    const goalData = unwrapList(goalResponse);
    const reportData = unwrapList(reportResponse);
    const statsData = unwrapPayload<Record<string, any>>(statsResponse, {});
    const recordData = unwrapList(recordsResponse);

    auth.user = meData ?? auth.user;

    const profile = meData?.profile;
    const height = profile?.height_cm ? Number(profile.height_cm) : 0;
    const weight = profile?.weight_kg ? Number(profile.weight_kg) : 0;
    if (height > 0 && weight > 0) {
      nutritionSummary.bmi = (weight / ((height / 100) * (height / 100))).toFixed(1);
    }

    const health = meData?.health_condition;
    if (health?.has_diabetes) {
      nutritionSummary.goal_hint = "优先控制碳水与添加糖";
    } else if (health?.has_hypertension) {
      nutritionSummary.goal_hint = "优先控制钠摄入";
    } else if (health?.has_hyperlipidemia) {
      nutritionSummary.goal_hint = "优先控制脂肪摄入";
    } else {
      nutritionSummary.goal_hint = "保持均衡饮食";
    }

    nutritionSummary.calorie_target = nutritionData?.calorie_target ?? "-";
    nutritionSummary.protein_target = nutritionData?.protein_target ?? "-";

    recommendations.value = finalRecommendationData.map((item: Record<string, any>) => ({
      recipe_id: Number(item.recipe_id),
      title: item.title,
      reason_text: item.reason_text,
      meal_type: item.meal_type || item.recipe?.meal_type || "lunch",
    }));

    favoriteItems.value = favoriteData;
    favoriteIds.value = favoriteData.map((item: Record<string, any>) => Number(item.id));
    favoriteCount.value = favoriteData.length;
    goals.value = goalData;
    reportTasks.value = reportData;
    recentRecords.value = recordData;

    const trend = Array.isArray(statsData?.trend) ? statsData.trend : [];
    weekTrend.value = trend;
    const today = trend[trend.length - 1];
    todayMetrics.energy = Number(today?.energy || 0);
    todayMetrics.protein = Number(today?.protein || 0);
    todayMetrics.fat = Number(today?.fat || 0);
    todayMetrics.carbohydrate = Number(today?.carbohydrate || 0);
    triggerDashboardRefreshPulse();

    trackEvent({ behavior_type: "view", context_scene: "home" }).catch(() => undefined);
  } catch (error) {
    notifyLoadError("首页数据");
  } finally {
    dashboardReady.value = true;
    loadingDashboard.value = false;
  }
}

function triggerDashboardRefreshPulse() {
  dashboardRefreshPulse.value = false;
  if (dashboardPulseTimer) {
    window.clearTimeout(dashboardPulseTimer);
  }
  requestAnimationFrame(() => {
    dashboardRefreshPulse.value = true;
    dashboardPulseTimer = window.setTimeout(() => {
      dashboardRefreshPulse.value = false;
      dashboardPulseTimer = null;
    }, 900);
  });
}

async function showReason(recipeId: number) {
  try {
    const response = await explainRecommendation(recipeId);
    const reasonData = unwrapPayload<Record<string, any>>(response, {});
    await ElMessageBox.alert(reasonData?.reason_text || "暂无推荐理由", "推荐说明", {
      confirmButtonText: "知道了",
    });
  } catch (error) {
    notifyLoadError("推荐说明");
  }
}

async function openRecipeDetail(item: { recipe_id: number; title: string; reason_text: string }) {
  selectedRecipeId.value = item.recipe_id;
  selectedRecipe.value = {
    id: item.recipe_id,
    title: item.title,
    description: item.reason_text,
  };
  selectedReasonText.value = item.reason_text;
  detailVisible.value = true;
}

function openFavoriteDetail(recipe: Record<string, any>) {
  selectedRecipeId.value = Number(recipe.id);
  selectedRecipe.value = recipe;
  selectedReasonText.value = "";
  detailVisible.value = true;
}

function addToRecord(recipe: Record<string, any>) {
  router.push({
    path: "/records",
    query: {
      recipe_id: String(recipe.id),
      meal_type: recipe.meal_type || "lunch",
      note: recipe.title || "",
      source: "home",
      from_title: recipe.title || "",
    },
  });
}

function goToNextMealRecord() {
  router.push({
    path: "/records",
    query: {
      meal_type: nextMealFocusType.value,
      note: `今天的${mealTypeLabel(nextMealFocusType.value)}`,
      source: "home",
      from_title: todaySuggestedRecipe.value?.title || "",
    },
  });
}

function setExtensionTab(tab: ExtensionTabKey) {
  extensionTabTouched.value = true;
  extensionTab.value = tab;
}

function openAssistantForTodayPlan() {
  const prompt = [
    "请基于我当前首页状态，用非常直接、可执行的话告诉我今天下一步怎么做。",
    `今天已记录餐次：${todayCompletedMealCount.value}。`,
    `当前建议优先补：${mealTypeLabel(nextMealFocusType.value)}。`,
    `今日热量：${formatMetric(todayMetrics.energy, "kcal")}，目标：${formatMetric(calorieTargetNumber.value, "kcal")}。`,
    `今日蛋白：${formatMetric(todayMetrics.protein, "g")}，目标：${formatMetric(proteinTargetNumber.value, "g")}。`,
    todaySuggestedRecipe.value ? `当前更省事的下一餐候选：${todaySuggestedRecipe.value.title}。` : "当前还没有明确的下一餐候选。",
    "请输出三部分：1）一句话判断我现在最该做什么；2）为什么；3）我点进记录页后应该怎么记。",
  ].join("\n");

  router.push({
    path: "/assistant",
    query: {
      source: "home_today_workbench",
      prompt,
    },
  });
}

function handleFavoriteChange(payload: { recipeId: number; favorited: boolean }) {
  if (payload.favorited && !favoriteIds.value.includes(payload.recipeId)) {
    favoriteIds.value = [...favoriteIds.value, payload.recipeId];
    favoriteCount.value += 1;
    return;
  }
  if (!payload.favorited) {
    favoriteIds.value = favoriteIds.value.filter((id) => id !== payload.recipeId);
    favoriteItems.value = favoriteItems.value.filter((item) => Number(item.id) !== payload.recipeId);
    favoriteCount.value = Math.max(0, favoriteCount.value - 1);
  }
}

onMounted(loadDashboard);

onBeforeUnmount(() => {
  if (dashboardPulseTimer) {
    window.clearTimeout(dashboardPulseTimer);
    dashboardPulseTimer = null;
  }
});
</script>

<style scoped>
/* ── 全局容器 ─────────────────────────────────── */
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* ── 顶部问候栏 ───────────────────────────────── */
.greeting-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 28px;
  background: rgba(255, 255, 255, 0.9);
  border-bottom: 1px solid rgba(16, 34, 42, 0.07);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 10;
  flex-wrap: wrap;
}

.greeting-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.greeting-name {
  margin: 0;
  font-size: clamp(18px, 2vw, 24px);
  font-weight: 700;
  color: #173042;
  line-height: 1.2;
}

.greeting-sub {
  margin: 0;
  font-size: 13px;
  color: #5a7a8a;
  line-height: 1.5;
  max-width: 540px;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.greeting-right {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-shrink: 0;
}

/* ── 双栏主体布局 ─────────────────────────────── */
.main-layout {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 0;
  min-height: calc(100vh - 110px);
  align-items: start;
}

/* ── 左侧栏 ───────────────────────────────────── */
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 16px 20px 20px;
  border-right: 1px solid rgba(16, 34, 42, 0.07);
  position: sticky;
  top: 60px;
  max-height: calc(100vh - 60px);
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(16, 34, 42, 0.1) transparent;
}

.sidebar-card {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(16, 34, 42, 0.08);
  border-radius: 20px;
  padding: 16px;
  box-shadow: 0 4px 16px rgba(15, 30, 39, 0.05);
}

.sidebar-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}

.card-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #5a7a8a;
}

/* 今日状态卡 */
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.badge-active {
  background: rgba(224, 247, 238, 0.9);
  color: #1d6f5f;
}

.badge-muted {
  background: rgba(232, 241, 247, 0.9);
  color: #5a7a8a;
}

/* 营养进度行 */
.nutrition-rows {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 14px;
}

.nutrition-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nutrition-row-head {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.nutrition-row-head span {
  font-size: 11px;
  color: #5a7a8a;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  flex-shrink: 0;
}

.nutrition-row-head strong {
  font-size: 16px;
  font-weight: 700;
  color: #173042;
  flex: 1;
}

.nutrition-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-style: normal;
  background: #e8f1f7;
  color: #24566a;
  flex-shrink: 0;
}

.nutrition-row.tone-success .nutrition-badge { background: rgba(224, 247, 238, 0.9); color: #1d6f5f; }
.nutrition-row.tone-warning .nutrition-badge { background: rgba(255, 237, 218, 0.9); color: #b97326; }
.nutrition-row.tone-steady .nutrition-badge { background: rgba(222, 235, 248, 0.9); color: #2a5f8a; }

.nutrition-bar-track {
  height: 5px;
  background: rgba(16, 34, 42, 0.08);
  border-radius: 999px;
  overflow: hidden;
}

.nutrition-bar-fill {
  height: 100%;
  border-radius: 999px;
  background: #3e9bd4;
  transition: width 0.6s cubic-bezier(0.22, 1, 0.36, 1);
}

.nutrition-row.tone-success .nutrition-bar-fill { background: #30b57a; }
.nutrition-row.tone-warning .nutrition-bar-fill { background: #e6914a; }
.nutrition-row.tone-muted .nutrition-bar-fill { background: rgba(16, 34, 42, 0.15); }

.nutrition-copy {
  margin: 0;
  font-size: 11px;
  color: #7a96a4;
  line-height: 1.4;
}

/* 四餐打卡 */
.meal-checklist {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6px;
}

.meal-check-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 10px;
  border-radius: 12px;
  background: rgba(247, 251, 255, 0.9);
  border: 1px solid rgba(16, 34, 42, 0.07);
  font-size: 12px;
}

.meal-check-item.done {
  background: rgba(224, 247, 238, 0.8);
  border-color: rgba(31, 120, 89, 0.14);
}

.meal-check-item.focus {
  background: rgba(255, 245, 231, 0.9);
  border-color: rgba(185, 115, 38, 0.2);
}

.meal-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: rgba(16, 34, 42, 0.2);
  flex-shrink: 0;
}

.meal-check-item.done .meal-dot { background: #30b57a; }
.meal-check-item.focus .meal-dot { background: #e6914a; }

.meal-label {
  flex: 1;
  color: #24566a;
  font-weight: 600;
}

.meal-status {
  font-size: 11px;
  color: #7a96a4;
  font-weight: 700;
}

.meal-check-item.done .meal-status { color: #1d6f5f; }
.meal-check-item.focus .meal-status { color: #b97326; }

/* 目标卡 */
.goal-name {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: #173042;
  margin-bottom: 4px;
}

.goal-desc {
  margin: 0 0 10px;
  font-size: 12px;
  color: #5a7a8a;
  line-height: 1.5;
}

.goal-progress-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 12px;
  color: #5a7a8a;
}

.goal-progress-badge {
  margin-left: auto;
}

.goal-empty {
  margin: 0;
  font-size: 13px;
  color: #7a96a4;
}

/* 快捷操作 */
.quick-btn-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 8px;
}

.quick-btn {
  width: 100%;
  font-size: 12px !important;
}

/* 起步引导 */
.onboarding-steps {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 8px;
}

.onboarding-step {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(247, 251, 255, 0.9);
  border: 1px solid rgba(16, 34, 42, 0.06);
  border-radius: 14px;
}

.onboarding-step strong {
  display: block;
  font-size: 13px;
  color: #173042;
  margin-bottom: 2px;
}

.onboarding-step p {
  margin: 0;
  font-size: 11px;
  color: #7a96a4;
  line-height: 1.4;
}

/* ── 右侧主内容区 ─────────────────────────────── */
.main-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px 24px 28px;
  min-height: 0;
}

/* 工作台标题区 */
.workbench-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.workbench-headline {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.workbench-kicker {
  font-size: 11px;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #2f6672;
  font-weight: 700;
}

.workbench-headline strong {
  font-size: clamp(22px, 2.4vw, 30px);
  font-weight: 700;
  color: #173042;
  line-height: 1.2;
}

.workbench-headline p {
  margin: 0;
  font-size: 13px;
  color: #5a7a8a;
  line-height: 1.6;
  max-width: 480px;
}

.workbench-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
  padding-top: 4px;
}

/* 四餐横排 */
.meal-progress-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.meal-progress-card {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(16, 34, 42, 0.08);
  cursor: pointer;
  transition:
    transform 0.3s cubic-bezier(0.22, 1.2, 0.36, 1),
    box-shadow 0.3s ease,
    border-color 0.25s ease,
    background 0.25s ease;
}

.meal-progress-card:hover {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 16px 32px rgba(15, 30, 39, 0.1);
}

.meal-card-label {
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #5a7a8a;
  font-weight: 700;
}

.meal-progress-card strong {
  display: block;
  margin-top: 8px;
  font-size: 17px;
  font-weight: 700;
  color: #173042;
}

.meal-progress-card p {
  margin: 5px 0 0;
  font-size: 12px;
  color: #7a96a4;
  line-height: 1.5;
}

.meal-progress-card.done {
  background: rgba(224, 247, 238, 0.85);
  border-color: rgba(31, 120, 89, 0.16);
}

.meal-progress-card.done strong { color: #1d6f5f; }

.meal-progress-card.active {
  background: rgba(255, 245, 231, 0.9);
  border-color: rgba(185, 115, 38, 0.22);
  box-shadow: 0 10px 28px rgba(185, 115, 38, 0.1);
}

.meal-progress-card.active strong { color: #b97326; }

/* 推荐菜谱区 */
.section-block {
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(16, 34, 42, 0.08);
  border-radius: 22px;
  padding: 20px;
  box-shadow: 0 4px 16px rgba(15, 30, 39, 0.05);
}

.section-block-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.section-block-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #173042;
}

.section-block-actions {
  display: flex;
  gap: 4px;
}

.recommend-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.recommend-card-h {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.07);
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition:
    transform 0.3s cubic-bezier(0.22, 1.2, 0.36, 1),
    box-shadow 0.3s ease;
  position: relative;
  overflow: hidden;
}

.recommend-card-h::after {
  content: "";
  position: absolute;
  inset: auto -24% -56% auto;
  width: 130px;
  height: 130px;
  border-radius: 999px;
  background: rgba(87, 181, 231, 0.08);
  pointer-events: none;
}

.recommend-card-h:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 28px rgba(15, 30, 39, 0.1);
}

.recommend-card-h strong {
  font-size: 15px;
  font-weight: 700;
  color: #173042;
  line-height: 1.3;
}

.recommend-card-h p {
  margin: 0;
  font-size: 12px;
  color: #5a7a8a;
  line-height: 1.5;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.recommend-card-actions {
  display: flex;
  gap: 2px;
  margin-top: 6px;
}

/* 下方双列 */
.lower-grid {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}

/* 下一餐推荐 */
.next-meal-card {
  padding: 18px;
  border-radius: 20px;
  background:
    radial-gradient(circle at top right, rgba(87, 181, 231, 0.12), transparent 40%),
    rgba(247, 251, 255, 0.94);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 4px 16px rgba(15, 30, 39, 0.05);
  display: flex;
  flex-direction: column;
  gap: 6px;
  transition: transform 0.3s cubic-bezier(0.22, 1.2, 0.36, 1), box-shadow 0.3s ease;
}

.next-meal-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 28px rgba(15, 30, 39, 0.1);
}

.next-meal-card strong {
  font-size: 18px;
  font-weight: 700;
  color: #173042;
  line-height: 1.3;
}

.next-meal-card p {
  margin: 0;
  font-size: 12px;
  color: #5a7a8a;
  line-height: 1.6;
  flex: 1;
}

.next-meal-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  flex-wrap: wrap;
}

/* 延展工作区 */
.extension-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(16, 34, 42, 0.08);
  border-radius: 22px;
  padding: 18px;
  box-shadow: 0 4px 16px rgba(15, 30, 39, 0.05);
}

.extension-tab-strip {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.extension-tab {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 12px;
  border-radius: 12px;
  border: 1px solid rgba(16, 34, 42, 0.08);
  background: rgba(247, 251, 255, 0.88);
  color: #234;
  text-align: left;
  cursor: pointer;
  flex-shrink: 0;
  transition:
    transform 0.25s cubic-bezier(0.22, 1.2, 0.36, 1),
    border-color 0.2s ease,
    box-shadow 0.25s ease,
    background 0.2s ease;
}

.extension-tab:hover {
  transform: translateY(-2px);
  border-color: rgba(23, 48, 66, 0.16);
  box-shadow: 0 8px 20px rgba(15, 30, 39, 0.08);
}

.extension-tab span {
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #5a7a8a;
}

.extension-tab strong {
  font-size: 12px;
  line-height: 1.3;
  font-weight: 600;
}

.extension-tab.active {
  background: #173042;
  color: #fff;
  border-color: #173042;
  box-shadow: 0 8px 24px rgba(23, 48, 66, 0.22);
}

.extension-tab.active span {
  color: rgba(255, 255, 255, 0.65);
}

.extension-body {
  min-height: 140px;
}

/* 延展列表项 */
.shortcut-list,
.record-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.shortcut-item,
.record-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
  transition: transform 0.25s cubic-bezier(0.22, 1.2, 0.36, 1), box-shadow 0.25s ease;
}

.interactive-shortcut-item:hover,
.interactive-record-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 22px rgba(15, 30, 39, 0.08);
}

.shortcut-item strong,
.record-item strong {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #173042;
  margin-bottom: 2px;
}

.shortcut-item p,
.record-item p {
  margin: 0;
  font-size: 12px;
  color: #7a96a4;
  line-height: 1.4;
}

.shortcut-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.record-item > span {
  font-size: 11px;
  color: #7a96a4;
  flex-shrink: 0;
  padding-top: 2px;
}

/* 目标/报表 focus box */
.focus-box {
  padding: 14px 16px;
  border-radius: 16px;
  background: rgba(247, 251, 255, 0.92);
  border: 1px solid rgba(16, 34, 42, 0.06);
}

.focus-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.focus-topline strong {
  font-size: 16px;
  font-weight: 700;
  color: #173042;
}

.focus-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  color: #24566a;
  background: #e8f1f7;
}

.goal-progress-badge {
  background: rgba(224, 247, 238, 0.9);
  color: #1d6f5f;
}

.focus-box p {
  margin: 0 0 10px;
  font-size: 13px;
  color: #5a7a8a;
  line-height: 1.55;
}

.progress-line {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 12px;
  color: #5a7a8a;
}

.focus-box a {
  display: inline-block;
  margin-top: 10px;
  color: #173042;
  font-weight: 700;
  text-decoration: none;
}

.status-card.is-refresh-pulse .meal-check-item {
  animation: dashboard-card-pulse 0.86s cubic-bezier(0.22, 1.2, 0.36, 1);
}

/* ── 响应式 ───────────────────────────────────── */
@media (max-width: 1200px) {
  .main-layout {
    grid-template-columns: 260px minmax(0, 1fr);
  }

  .recommend-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 1024px) {
  .lower-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .main-layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: static;
    max-height: none;
    padding: 16px;
    border-right: none;
    border-bottom: 1px solid rgba(16, 34, 42, 0.07);
  }

  .meal-progress-row,
  .recommend-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .greeting-bar {
    padding: 14px 16px;
    flex-direction: column;
    align-items: flex-start;
  }

  .main-content {
    padding: 14px 16px 20px;
  }

  .meal-progress-row,
  .recommend-row,
  .meal-checklist {
    grid-template-columns: 1fr 1fr;
  }

  .workbench-header {
    flex-direction: column;
  }
}

@keyframes dashboard-card-pulse {
  0% {
    transform: translateY(0) scale(1);
    box-shadow: 0 0 0 rgba(87, 181, 231, 0);
  }
  35% {
    transform: translateY(-3px) scale(1.015);
    box-shadow: 0 18px 34px rgba(87, 181, 231, 0.14);
  }
  100% {
    transform: translateY(0) scale(1);
    box-shadow: 0 0 0 rgba(87, 181, 231, 0);
  }
}
</style>
