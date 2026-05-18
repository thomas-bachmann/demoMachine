<script setup>
import { ref, computed, nextTick } from 'vue'

const props = defineProps({
  machineState: { type: Object, default: () => ({}) }
})

const isOpen = ref(false)
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesContainer = ref(null)
const sessionId = ref(null)

const displayMessages = computed(() => {
  return messages.value.map((msg, idx) => ({
    ...msg,
    id: idx
  }))
})

function toggleDrawer() {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    nextTick(() => scrollToBottom())
  }
}

function closeDrawer() {
  isOpen.value = false
}

async function scrollToBottom() {
  if (messagesContainer.value) {
    await nextTick()
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

async function sendMessage() {
  if (!inputMessage.value.trim() || loading.value) return

  const userMsg = inputMessage.value.trim()
  inputMessage.value = ''
  
  messages.value.push({
    role: 'user',
    content: userMsg,
    timestamp: new Date().toLocaleTimeString()
  })

  await scrollToBottom()
  
  loading.value = true
  try {
    const res = await fetch('/api/llm-chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userMsg,
        machine_state: props.machineState,
        session_id: sessionId.value
      })
    })

    if (res.ok) {
      const data = await res.json()
      sessionId.value = data.session_id
      messages.value.push({
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toLocaleTimeString()
      })
    } else {
      messages.value.push({
        role: 'assistant',
        content: '❌ Erreur lors de la communication',
        timestamp: new Date().toLocaleTimeString()
      })
    }
  } catch (error) {
    console.error('Chat error:', error)
    messages.value.push({
      role: 'assistant',
      content: '❌ Erreur de connexion',
      timestamp: new Date().toLocaleTimeString()
    })
  }

  loading.value = false
  await scrollToBottom()
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}
</script>

<template>
  <div class="llm-chat-system">
    <!-- Bouton toggle fixe -->
    <button class="chat-toggle-button" @click="toggleDrawer" :aria-pressed="isOpen">
      <span class="chat-icon">💬</span>
      <span v-if="messages.length > 0" class="message-badge">{{ messages.length }}</span>
    </button>

    <!-- Drawer -->
    <transition name="drawer-slide">
      <div v-if="isOpen" class="chat-drawer">
        <!-- En-tête -->
        <div class="drawer-header">
          <h3>AI Assistant</h3>
          <button class="close-button" @click="closeDrawer" aria-label="Close chat">✕</button>
        </div>

        <!-- Messages -->
        <div ref="messagesContainer" class="messages-container">
          <div v-if="messages.length === 0" class="empty-state">
            <p>👋 Bienvenue! Je peux vous aider à:</p>
            <ul>
              <li>Contrôler les moteurs</li>
              <li>Vérifier l'état de la machine</li>
              <li>Gérer les arrêts d'urgence</li>
              <li>Naviguer vers les menus appropriés</li>
            </ul>
          </div>

          <div v-for="msg in displayMessages" :key="msg.id" class="message" :class="`message-${msg.role}`">
            <div class="message-header">
              <span class="message-role">{{ msg.role === 'user' ? '👤 Vous' : '🤖 Assistant' }}</span>
              <span class="message-time">{{ msg.timestamp }}</span>
            </div>
            <div class="message-content">{{ msg.content }}</div>
          </div>

          <div v-if="loading" class="message message-assistant">
            <div class="spinner"></div>
            <span>En attente de réponse...</span>
          </div>
        </div>

        <!-- Input -->
        <div class="input-area">
          <textarea
            v-model="inputMessage"
            placeholder="Posez une question... (Entrée pour envoyer, Maj+Entrée pour nouvelle ligne)"
            class="message-input"
            :disabled="loading"
            @keydown="handleKeydown"
            rows="2"
          ></textarea>
          <button class="send-button" @click="sendMessage" :disabled="!inputMessage.trim() || loading">
            {{ loading ? '⏳' : '📤' }}
          </button>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.llm-chat-system {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
  font-family: 'Rajdhani', sans-serif;
}

.chat-toggle-button {
  position: relative;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #58d0ff, #2bc5c1);
  border: none;
  color: #0a1218;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(88, 208, 255, 0.4);
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-toggle-button:hover {
  transform: scale(1.1);
  box-shadow: 0 8px 24px rgba(88, 208, 255, 0.5);
}

.chat-toggle-button:active {
  transform: scale(0.95);
}

.message-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #ff5f6d;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.chat-drawer {
  position: fixed;
  bottom: 90px;
  right: 20px;
  width: 360px;
  height: 480px;
  background: linear-gradient(150deg, rgba(33, 49, 67, 0.98), rgba(17, 30, 45, 0.98));
  border: 1px solid rgba(134, 176, 214, 0.3);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid rgba(134, 176, 214, 0.2);
  background: linear-gradient(150deg, rgba(21, 60, 90, 0.6), rgba(15, 40, 60, 0.6));
}

.drawer-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #dceeff;
}

.close-button {
  background: none;
  border: none;
  color: #9bb4cd;
  font-size: 20px;
  cursor: pointer;
  padding: 4px 8px;
  transition: color 0.2s;
}

.close-button:hover {
  color: #dceeff;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.empty-state {
  color: #9bb4cd;
  font-size: 0.9rem;
  line-height: 1.5;
}

.empty-state p {
  margin: 0 0 8px;
  font-weight: 500;
}

.empty-state ul {
  margin: 0;
  padding-left: 20px;
  list-style: disc;
}

.empty-state li {
  margin: 4px 0;
}

.message {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.message-user {
  align-items: flex-end;
}

.message-assistant {
  align-items: flex-start;
}

.message-header {
  display: flex;
  gap: 8px;
  font-size: 0.75rem;
  color: #7a8fa0;
}

.message-role {
  font-weight: 600;
}

.message-time {
  opacity: 0.7;
}

.message-content {
  max-width: 85%;
  padding: 10px 12px;
  border-radius: 8px;
  line-height: 1.4;
  word-wrap: break-word;
  white-space: pre-wrap;
  font-size: 0.9rem;
}

.message-user .message-content {
  background: linear-gradient(135deg, #58d0ff, #2bc5c1);
  color: #0a1218;
  font-weight: 500;
}

.message-assistant .message-content {
  background: rgba(88, 208, 255, 0.1);
  color: #dceeff;
  border: 1px solid rgba(88, 208, 255, 0.2);
}

.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(88, 208, 255, 0.3);
  border-top-color: #58d0ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.input-area {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid rgba(134, 176, 214, 0.2);
  background: rgba(0, 0, 0, 0.2);
}

.message-input {
  flex: 1;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(121, 147, 176, 0.3);
  border-radius: 6px;
  color: #dceeff;
  font-family: 'Rajdhani', sans-serif;
  font-size: 0.9rem;
  resize: none;
  transition: border-color 0.2s;
}

.message-input:focus {
  outline: none;
  border-color: #58d0ff;
}

.message-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.send-button {
  padding: 8px 12px;
  background: linear-gradient(135deg, #58d0ff, #2bc5c1);
  border: none;
  border-radius: 6px;
  color: #0a1218;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 600;
}

.send-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(88, 208, 255, 0.4);
}

.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Animations */
.drawer-slide-enter-active,
.drawer-slide-leave-active {
  transition: all 0.3s ease;
}

.drawer-slide-enter-from {
  transform: translateY(500px);
  opacity: 0;
}

.drawer-slide-leave-to {
  transform: translateY(500px);
  opacity: 0;
}

/* Scrollbar styling */
.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: transparent;
}

.messages-container::-webkit-scrollbar-thumb {
  background: rgba(88, 208, 255, 0.3);
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: rgba(88, 208, 255, 0.5);
}

@media (max-width: 480px) {
  .chat-drawer {
    width: calc(100vw - 40px);
    height: calc(100vh - 150px);
    right: 20px;
    bottom: 90px;
  }

  .message-content {
    max-width: 100%;
  }
}
</style>
