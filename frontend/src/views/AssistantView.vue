<template>
  <section class="page">
    <div class="head">
      <div>
        <p class="tag">AI Assistant</p>
        <h2>AI 营养助手</h2>
        <p class="desc">基于你的健康档案、饮食记录和目标，获取个性化营养建议。</p>
      </div>
      <el-button @click="startNewConversation" :loading="creating">新建对话</el-button>
    </div>

    <div class="chat-layout">
      <!-- 对话列表 -->
      <aside class="sidebar">
        <div class="sidebar-head">
          <strong>历史对话</strong>
        </div>
        <div class="conv-list">
          <div
            v-for="conv in conversations"
            :key="conv.id"
            class="conv-item"
            :class="{ active: currentConvId === conv.id }"
            @click="selectConversation(conv)"
          >
            <span class="conv-title">{{ conv.title }}</span>
            <el-button
              text
              type="danger"
              size="small"
              class="conv-delete"
              :loading="deletingId === conv.id"
              @click.stop="removeConversation(conv.id)"
            >删</el-button>
          </div>
          <div v-if="!conversations.length" class="conv-empty">暂无对话记录</div>
        </div>
      </aside>

      <!-- 聊天区域 -->
      <div class="chat-area">
        <div v-if="!currentConvId" class="chat-placeholder">
          <div class="placeholder-inner">
            <p class="placeholder-icon">🥗</p>
            <strong>和 AI 营养师开始对话</strong>
            <p>点击「新建对话」，告诉我你的饮食困惑或营养问题，我会结合你的健康档案给出个性化建议。</p>
            <el-button type="primary" @click="startNewConversation" :loading="creating">开始对话</el-button>
          </div>
        </div>

        <template v-else>
          <div class="messages" ref="messagesEl">
            <div v-if="loadingMessages" class="msg-loading">加载中...</div>
            <template v-else>
              <div
                v-for="msg in messages"
                :key="msg.id"
                class="msg-row"
                :class="msg.role === 'user' ? 'msg-user' : 'msg-assistant'"
              >
                <div class="bubble">
                  <div class="bubble-content" v-html="renderContent(msg.content)"></div>
                </div>
              </div>
              <!-- 流式输出中的消息 -->
              <div v-if="streamingContent" class="msg-row msg-assistant">
                <div class="bubble">
                  <div class="bubble-content" v-html="renderContent(streamingContent)"></div>
                  <span class="typing-dot">▋</span>
                </div>
              </div>
            </template>
          </div>

          <div class="input-area">
            <el-input
              v-model="inputText"
              type="textarea"
              :rows="2"
              :autosize="{ minRows: 2, maxRows: 5 }"
              placeholder="输入你的问题，例如：我最近蛋白质摄入够吗？"
              :disabled="streaming"
              @keydown.enter.exact.prevent="sendMessage"
            />
            <el-button
              type="primary"
              :loading="streaming"
              :disabled="!inputText.trim()"
              @click="sendMessage"
            >{{ streaming ? '回复中...' : '发送' }}</el-button>
          </div>
        </template>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { nextTick, ref, onMounted } from "vue";
import { chatSSE, createConversation, deleteConversation, getConversation, listConversations } from "../api/assistant";
import { notifyActionError, notifyActionSuccess } from "../lib/feedback";
import { ElMessageBox } from "element-plus";

interface Conversation { id: number; title: string; created_at: string; updated_at: string }
interface Message { id: number; role: string; content: string; created_at: string }

const conversations = ref<Conversation[]>([]);
const currentConvId = ref<number | null>(null);
const messages = ref<Message[]>([]);
const inputText = ref("");
const streaming = ref(false);
const streamingContent = ref("");
const creating = ref(false);
const deletingId = ref<number | null>(null);
const loadingMessages = ref(false);
const messagesEl = ref<HTMLElement | null>(null);

function renderContent(text: string) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>");
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesEl.value) {
      messagesEl.value.scrollTop = messagesEl.value.scrollHeight;
    }
  });
}

async function loadConversations() {
  try {
    const res = await listConversations();
    conversations.value = res.data ?? [];
  } catch {
    // silent
  }
}

async function selectConversation(conv: Conversation) {
  currentConvId.value = conv.id;
  loadingMessages.value = true;
  try {
    const res = await getConversation(conv.id);
    messages.value = (res.data?.messages ?? []).filter((m: Message) => m.role !== "system");
    scrollToBottom();
  } catch {
    notifyActionError("加载对话");
  } finally {
    loadingMessages.value = false;
  }
}

async function startNewConversation() {
  creating.value = true;
  try {
    const res = await createConversation();
    const conv = res.data;
    conversations.value = [conv, ...conversations.value];
    currentConvId.value = conv.id;
    messages.value = [];
  } catch {
    notifyActionError("创建对话");
  } finally {
    creating.value = false;
  }
}

async function removeConversation(id: number) {
  try {
    await ElMessageBox.confirm("确认删除这条对话记录？", "删除对话", { type: "warning", confirmButtonText: "删除", cancelButtonText: "取消" });
  } catch { return; }
  try {
    deletingId.value = id;
    await deleteConversation(id);
    conversations.value = conversations.value.filter((c) => c.id !== id);
    if (currentConvId.value === id) {
      currentConvId.value = null;
      messages.value = [];
    }
    notifyActionSuccess("对话已删除");
  } catch {
    notifyActionError("删除对话");
  } finally {
    deletingId.value = null;
  }
}

async function sendMessage() {
  const text = inputText.value.trim();
  if (!text || !currentConvId.value || streaming.value) return;

  inputText.value = "";
  messages.value.push({ id: Date.now(), role: "user", content: text, created_at: new Date().toISOString() });
  scrollToBottom();

  streaming.value = true;
  streamingContent.value = "";

  chatSSE(
    currentConvId.value,
    text,
    (chunk) => {
      streamingContent.value += chunk;
      scrollToBottom();
    },
    () => {
      messages.value.push({ id: Date.now() + 1, role: "assistant", content: streamingContent.value, created_at: new Date().toISOString() });
      streamingContent.value = "";
      streaming.value = false;
      // Update conversation title in list
      loadConversations();
      scrollToBottom();
    },
    (err) => {
      streamingContent.value = "";
      streaming.value = false;
      notifyActionError(err || "AI 助手");
    },
  );
}

onMounted(loadConversations);
</script>

<style scoped>
.page {
  display: grid;
  gap: 16px;
  height: calc(100vh - 120px);
  grid-template-rows: auto 1fr;
}

.head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.tag {
  margin: 0 0 6px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-size: 12px;
  color: #3e6d7f;
}

h2 { margin: 0; font-size: 30px; }

.desc {
  margin: 8px 0 0;
  color: #476072;
  line-height: 1.65;
}

.chat-layout {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 14px;
  min-height: 0;
}

/* Sidebar */
.sidebar {
  display: flex;
  flex-direction: column;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 8px 30px rgba(15, 30, 39, 0.06);
  overflow: hidden;
}

.sidebar-head {
  padding: 14px 16px 10px;
  font-size: 13px;
  color: #476072;
  border-bottom: 1px solid rgba(16, 34, 42, 0.06);
}

.conv-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.conv-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
}

.conv-item:hover { background: rgba(16, 34, 42, 0.05); }
.conv-item.active { background: rgba(29, 111, 95, 0.1); }

.conv-title {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-delete { opacity: 0; transition: opacity 0.15s; flex-shrink: 0; }
.conv-item:hover .conv-delete { opacity: 1; }

.conv-empty {
  padding: 20px 12px;
  font-size: 13px;
  color: #8a9faa;
  text-align: center;
}

/* Chat area */
.chat-area {
  display: flex;
  flex-direction: column;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(16, 34, 42, 0.08);
  box-shadow: 0 8px 30px rgba(15, 30, 39, 0.06);
  overflow: hidden;
  min-height: 0;
}

.chat-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-inner {
  text-align: center;
  max-width: 320px;
  padding: 32px;
}

.placeholder-icon { font-size: 48px; margin: 0 0 16px; }
.placeholder-inner strong { display: block; font-size: 18px; margin-bottom: 10px; }
.placeholder-inner p { color: #476072; line-height: 1.65; margin: 0 0 20px; }

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 0;
}

.msg-loading {
  text-align: center;
  color: #8a9faa;
  font-size: 13px;
  padding: 20px;
}

.msg-row { display: flex; }
.msg-user { justify-content: flex-end; }
.msg-assistant { justify-content: flex-start; }

.bubble {
  max-width: 72%;
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.7;
  position: relative;
}

.msg-user .bubble {
  background: #173042;
  color: #fff;
  border-bottom-right-radius: 4px;
}

.msg-assistant .bubble {
  background: #f0f6fa;
  color: #10202c;
  border-bottom-left-radius: 4px;
}

.bubble-content { word-break: break-word; }

.typing-dot {
  display: inline-block;
  animation: blink 0.8s step-end infinite;
  color: #3e6d7f;
  margin-left: 2px;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.input-area {
  display: flex;
  gap: 10px;
  padding: 14px 16px;
  border-top: 1px solid rgba(16, 34, 42, 0.06);
  align-items: flex-end;
}

.input-area :deep(.el-textarea) { flex: 1; }

@media (max-width: 768px) {
  .page { height: auto; }
  .chat-layout { grid-template-columns: 1fr; }
  .sidebar { max-height: 180px; }
  .chat-area { min-height: 60vh; }
  .bubble { max-width: 88%; }
}
</style>
