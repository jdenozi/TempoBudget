<template>
  <!-- Floating Help Button -->
  <div class="help-chat-container">
    <n-button
      v-if="!isOpen"
      type="primary"
      circle
      size="large"
      class="help-button"
      @click="isOpen = true"
      :aria-label="t('help.openChat')"
    >
      <n-icon :component="HelpCircleOutline" :size="24" />
    </n-button>

    <!-- Chat Drawer -->
    <n-drawer
      v-model:show="isOpen"
      :width="isMobile ? '100%' : 380"
      placement="right"
    >
      <n-drawer-content closable>
        <template #header>
          <n-flex align="center" :size="8">
            <n-icon :component="ChatbubbleEllipsesOutline" :size="20" />
            <span>{{ t('help.title') }}</span>
          </n-flex>
        </template>

        <div class="chat-content">
          <!-- Welcome message -->
          <div class="chat-message bot">
            <div class="message-content">
              {{ t('help.welcome') }}
            </div>
          </div>

          <!-- Conversation -->
          <div v-for="(msg, idx) in conversation" :key="idx" class="chat-message" :class="msg.from">
            <div class="message-content" v-html="msg.text"></div>
          </div>

          <!-- Quick Topics (shown when no conversation) -->
          <div v-if="conversation.length === 0" class="quick-topics">
            <div class="topics-label">{{ t('help.quickTopics') }}</div>
            <n-space vertical :size="8">
              <n-button
                v-for="topic in quickTopics"
                :key="topic.key"
                size="small"
                quaternary
                block
                class="topic-button"
                @click="handleTopicClick(topic)"
              >
                {{ topic.label }}
              </n-button>
            </n-space>
          </div>

          <!-- Back to topics button -->
          <n-button
            v-if="conversation.length > 0"
            size="small"
            quaternary
            @click="resetConversation"
            style="margin-top: 12px;"
          >
            ← {{ t('help.backToTopics') }}
          </n-button>
        </div>

        <!-- Input -->
        <template #footer>
          <n-input-group>
            <n-input
              v-model:value="userInput"
              :placeholder="t('help.placeholder')"
              @keyup.enter="handleSend"
            />
            <n-button type="primary" @click="handleSend" :disabled="!userInput.trim()">
              <n-icon :component="SendOutline" />
            </n-button>
          </n-input-group>
        </template>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  NButton, NDrawer, NDrawerContent, NIcon, NInput, NInputGroup, NSpace, NFlex
} from 'naive-ui'
import { HelpCircleOutline, ChatbubbleEllipsesOutline, SendOutline } from '@vicons/ionicons5'
import { useMobileDetect } from '@/composables/useMobileDetect'

const { t } = useI18n()
const { isMobile } = useMobileDetect()

const isOpen = ref(false)
const userInput = ref('')
const conversation = ref<{ from: 'user' | 'bot'; text: string }[]>([])

interface HelpTopic {
  key: string
  label: string
  keywords: string[]
  response: string
}

// Knowledge base
const helpTopics = computed<HelpTopic[]>(() => [
  {
    key: 'invoice',
    label: t('help.topics.invoice'),
    keywords: ['facture', 'invoice', 'créer facture', 'facturer', 'facturation'],
    response: t('help.responses.invoice'),
  },
  {
    key: 'quote',
    label: t('help.topics.quote'),
    keywords: ['devis', 'quote', 'créer devis', 'proposition'],
    response: t('help.responses.quote'),
  },
  {
    key: 'regime',
    label: t('help.topics.regime'),
    keywords: ['régime', 'regime', 'micro', 'eurl', 'sasu', 'statut', 'juridique'],
    response: t('help.responses.regime'),
  },
  {
    key: 'cotisations',
    label: t('help.topics.cotisations'),
    keywords: ['cotisation', 'urssaf', 'charges', 'social', 'contribution'],
    response: t('help.responses.cotisations'),
  },
  {
    key: 'acre',
    label: t('help.topics.acre'),
    keywords: ['acre', 'aide', 'création', 'réduction', 'première année'],
    response: t('help.responses.acre'),
  },
  {
    key: 'tva',
    label: t('help.topics.tva'),
    keywords: ['tva', 'taxe', 'franchise', 'assujetti'],
    response: t('help.responses.tva'),
  },
  {
    key: 'client',
    label: t('help.topics.client'),
    keywords: ['client', 'ajouter client', 'nouveau client', 'fiche client'],
    response: t('help.responses.client'),
  },
  {
    key: 'declaration',
    label: t('help.topics.declaration'),
    keywords: ['déclaration', 'déclarer', 'comptabiliser', 'échéance'],
    response: t('help.responses.declaration'),
  },
])

const quickTopics = computed(() => helpTopics.value.slice(0, 6))

function findResponse(input: string): string {
  const lowerInput = input.toLowerCase()

  for (const topic of helpTopics.value) {
    for (const keyword of topic.keywords) {
      if (lowerInput.includes(keyword.toLowerCase())) {
        return topic.response
      }
    }
  }

  return t('help.responses.notFound')
}

function handleTopicClick(topic: HelpTopic) {
  conversation.value.push({ from: 'user', text: topic.label })
  setTimeout(() => {
    conversation.value.push({ from: 'bot', text: topic.response })
  }, 300)
}

function handleSend() {
  const input = userInput.value.trim()
  if (!input) return

  conversation.value.push({ from: 'user', text: input })
  userInput.value = ''

  setTimeout(() => {
    const response = findResponse(input)
    conversation.value.push({ from: 'bot', text: response })
  }, 400)
}

function resetConversation() {
  conversation.value = []
}
</script>

<style scoped>
.help-chat-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;
}

.help-button {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.chat-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 0;
}

.chat-message {
  max-width: 85%;
}

.chat-message.user {
  align-self: flex-end;
}

.chat-message.bot {
  align-self: flex-start;
}

.message-content {
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
}

.chat-message.user .message-content {
  background: #18a058;
  color: white;
  border-bottom-right-radius: 4px;
}

.chat-message.bot .message-content {
  background: rgba(255, 255, 255, 0.08);
  border-bottom-left-radius: 4px;
}

.quick-topics {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.topics-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 10px;
}

.topic-button {
  text-align: left;
  justify-content: flex-start;
}
</style>
