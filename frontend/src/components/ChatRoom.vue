<!-- frontend/src/components/ChatRoom.vue -->
<template>
  <div class="chat-container">
    <div v-if="error" class="error-message">{{ error }}</div>
    <div class="chat-content" :class="{ 'blur-background': !isInitialized }">
      <vue-advanced-chat
        v-if="isInitialized"
        :current-user-id="displayName"
        :rooms="JSON.stringify(rooms)"
        :messages="JSON.stringify(chatMessages)"
        :room-id="currentRoomId"
        :show-audio="false"
        :show-files="false"
        :single-room="true"
        :styles="JSON.stringify(styles)"
        :messages-loaded="messagesLoaded"
        :message-actions="JSON.stringify([])"
        :menu-actions="JSON.stringify([])"
        :show-send-icon="true"
        :show-reaction-emojis="false"
        :show-emojis="false"
        theme="dark"
        height="100vh"
        @send-message="onMessage"
      />
    </div>
    <UserNameInput
      v-if="!isInitialized"
      @submit="initializeChat"
      class="name-input-overlay"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import { register } from "vue-advanced-chat";
import { useChatStore } from "../stores/chat";
import { useUsersStore } from "../stores/users";
import { storeToRefs } from "pinia";
import defaultAvatar from "@/assets/images/bust_in_silhouette.png";
import roomAvatar from "@/assets/images/night_with_stars.png";
import masterAvatar from "@/assets/images/sparkles.png";
import UserNameInput from "./UserNameInput.vue";
import { getAvatarForUser } from "../utils/avatar";

// 以下のコードは変更なし
register();

const isInitialized = ref(false);
const error = ref("");
const messagesLoaded = ref(true);

const chatStore = useChatStore();
const usersStore = useUsersStore();

const {
  currentRoomId,
  displayName,
  messages: storeMessages,
} = storeToRefs(chatStore);
const { activeUsers } = storeToRefs(usersStore);

// 以下の関数は既存のまま
const initializeChat = async (name) => {
  try {
    console.info("Attempting to enter bar");
    const success = await chatStore.enterBar(name);

    if (success) {
      console.info("Chat initialization successful");
      isInitialized.value = true;
      console.info("Starting periodic updates");
      chatStore.startPeriodicUpdates();
      console.info("Fetching active users");
      await usersStore.fetchActiveUsers();
    } else {
      throw new Error("チャットの初期化に失敗しました");
    }
  } catch (e) {
    console.error("Chat initialization error:", e);
    error.value = e.message || "チャットの初期化に失敗しました";
  }
};

const chatMessages = computed(() => {
  return storeMessages.value.map((msg) => ({
    _id: msg._id,
    content: msg.content,
    senderId: msg.senderId,
    username: msg.username,
    // timestamp: msg.timestamp,
    system: msg.system,
    avatar:
      msg.senderId === "master" ? masterAvatar : getAvatarForUser(msg.username),
  }));
});

const rooms = computed(() => {
  return [
    {
      roomId: currentRoomId.value,
      roomName: "深夜のテックバー",
      avatar: roomAvatar,
      users: activeUsers.value
        ? activeUsers.value.map((user) => ({
            _id: user.session_key,
            username: user.display_name,
            avatar: user.is_master ? masterAvatar : defaultAvatar,
            status: {
              state: "online",
              lastChanged: user.last_active,
            },
          }))
        : [],
      lastMessage: chatMessages.value[chatMessages.value.length - 1] || {
        content: "いらっしゃいませ！",
        senderId: "master",
        timestamp: new Date().toISOString(),
      },
      typingUsers: [],
    },
  ];
});

async function onMessage(event) {
  try {
    const eventData = event.detail?.[0];
    if (!eventData?.content) {
      console.error("Invalid message data:", event);
      return;
    }
    await chatStore.sendMessage(eventData.content);
  } catch (error) {
    console.error("Failed to send message:", error);
    error.value = error.message || "メッセージの送信に失敗しました";
  }
}

onMounted(() => {
  usersStore.fetchActiveUsers();
  chatStore.startPeriodicUpdates();
});

onUnmounted(() => {
  chatStore.stopPeriodicUpdates();
});
</script>

<style scoped>
.chat-container {
  height: 100vh;
  background-color: #1e1e2e;
  width: 100%;
  overflow: hidden;
  position: relative;
}

.chat-content {
  height: 100%;
  width: 100%;
}

.name-input-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1000;
  background-color: rgba(30, 30, 46, 0.95);
}

.blur-background {
  filter: blur(4px);
}

.error-message {
  color: #ff5555;
  padding: 1rem;
  text-align: center;
  background-color: rgba(255, 85, 85, 0.1);
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  z-index: 1001;
}
</style>
