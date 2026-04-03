<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">Pricing</p>
        <h2>选择你的套餐</h2>
        <p class="desc">免费版够用来体验，Pro 版让你的健康管理真正跑起来。</p>
      </div>
    </div>

    <div class="plans-grid">
      <!-- 免费版 -->
      <div class="plan-card">
        <div class="plan-header">
          <span class="plan-badge free">免费版</span>
          <div class="plan-price">
            <span class="price-amount">¥0</span>
            <span class="price-period">永久免费</span>
          </div>
        </div>
        <ul class="plan-features">
          <li class="feature-ok">AI 营养师对话 <strong>30 次 / 月</strong></li>
          <li class="feature-ok">个性化菜谱推荐</li>
          <li class="feature-ok">饮食记录与热量追踪</li>
          <li class="feature-ok">健康目标管理</li>
          <li class="feature-ok">周报数据看板</li>
          <li class="feature-ok">基础社区互动</li>
          <li class="feature-locked">月报（锁定）</li>
          <li class="feature-locked">PDF 报表导出（锁定）</li>
          <li class="feature-locked">Pro 专属菜谱（锁定）</li>
        </ul>
        <div class="plan-action">
          <el-button v-if="!auth.isAuthenticated" type="default" @click="router.push('/login')">免费注册</el-button>
          <el-button v-else-if="!auth.isPro" disabled>当前套餐</el-button>
          <el-button v-else type="default" disabled>基础版</el-button>
        </div>
      </div>

      <!-- Pro 版 -->
      <div class="plan-card plan-card-pro">
        <div class="plan-badge-row">
          <span class="plan-badge pro">Pro 版</span>
          <span class="plan-recommended">推荐</span>
        </div>
        <div class="plan-price">
          <span class="price-amount">¥25</span>
          <span class="price-period">/ 月</span>
        </div>
        <p class="price-annual">或 ¥199 / 年（节省 ¥101）</p>
        <ul class="plan-features">
          <li class="feature-ok"><strong>无限</strong> AI 营养师对话</li>
          <li class="feature-ok">个性化菜谱推荐</li>
          <li class="feature-ok">饮食记录与热量追踪</li>
          <li class="feature-ok">健康目标管理</li>
          <li class="feature-ok">周报 + <strong>月报</strong>数据看板</li>
          <li class="feature-ok"><strong>PDF 报表</strong>下载导出</li>
          <li class="feature-ok"><strong>Pro 专属菜谱</strong>（营养师精选）</li>
          <li class="feature-ok">社区全功能</li>
          <li class="feature-ok">优先客服支持</li>
        </ul>
        <div class="plan-action">
          <el-button v-if="auth.isPro" type="primary" disabled>当前套餐</el-button>
          <el-button v-else type="primary" @click="contactVisible = true">升级 Pro</el-button>
        </div>
      </div>
    </div>

    <div class="card note-card">
      <h3>关于升级</h3>
      <p>目前支持联系管理员手动升级账号。在线支付功能即将上线，敬请期待。</p>
      <p>升级后立即生效，AI 对话次数限制解除，Pro 专属菜谱可立即查看。</p>
    </div>

    <el-dialog v-model="contactVisible" title="升级 Pro 版" width="420px">
      <div class="contact-content">
        <p>请联系管理员升级你的账号：</p>
        <div class="contact-info">
          <div><span class="contact-label">你的账号：</span><strong>{{ auth.user?.username }}</strong></div>
          <div><span class="contact-label">当前套餐：</span><strong>免费版</strong></div>
        </div>
        <p class="contact-tip">将以上信息发送给管理员，管理员确认付款后即可完成升级。</p>
      </div>
      <template #footer>
        <el-button @click="contactVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const router = useRouter();
const contactVisible = ref(false);
</script>

<style scoped>
.page {
  display: grid;
  gap: 24px;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.tag {
  margin: 0 0 6px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-size: 12px;
  color: #3e6d7f;
}

h2 {
  margin: 0;
  font-size: 30px;
}

.desc {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.65;
}

.plans-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.plan-card {
  padding: 28px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.plan-card-pro {
  border-color: #3e6d7f;
  background: rgba(240, 248, 255, 0.92);
  box-shadow: 0 20px 60px rgba(62, 109, 127, 0.15);
}

.plan-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.plan-badge-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.plan-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
}

.plan-badge.free {
  background: #e8f4f8;
  color: #3e6d7f;
}

.plan-badge.pro {
  background: #3e6d7f;
  color: #fff;
}

.plan-recommended {
  font-size: 12px;
  color: #3e6d7f;
  font-weight: 600;
  background: rgba(62, 109, 127, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
}

.plan-price {
  display: flex;
  align-items: baseline;
  gap: 6px;
}

.price-amount {
  font-size: 36px;
  font-weight: 700;
  color: #173042;
}

.price-period {
  font-size: 14px;
  color: #5a7a8a;
}

.price-annual {
  margin: -12px 0 0;
  font-size: 13px;
  color: #5a7a8a;
}

.plan-features {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
}

.plan-features li {
  font-size: 14px;
  padding-left: 22px;
  position: relative;
  color: #2d4a5a;
}

.feature-ok::before {
  content: "✓";
  position: absolute;
  left: 0;
  color: #3e6d7f;
  font-weight: 700;
}

.feature-locked {
  color: #9ab0bb;
}

.feature-locked::before {
  content: "🔒";
  position: absolute;
  left: 0;
  font-size: 12px;
}

.plan-action {
  margin-top: auto;
}

.plan-action .el-button {
  width: 100%;
}

.card {
  padding: 20px 24px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 30, 39, 0.08);
}

.note-card h3 {
  margin: 0 0 12px;
  font-size: 18px;
}

.note-card p {
  margin: 0 0 8px;
  color: #476072;
  font-size: 14px;
  line-height: 1.6;
}

.contact-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.contact-info {
  background: #f0f8fc;
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 14px;
}

.contact-label {
  color: #5a7a8a;
}

.contact-tip {
  font-size: 13px;
  color: #7a9aaa;
}

@media (max-width: 640px) {
  .plans-grid {
    grid-template-columns: 1fr;
  }
}
</style>
