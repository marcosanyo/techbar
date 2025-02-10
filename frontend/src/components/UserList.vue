<!-- frontend/src/components/UserList.vue -->
<template>
  <div class="user-list">
    <div class="user-list-header">
      <h3>🥂 本日のお客様</h3>
    </div>
    <div class="user-list-content">
      <div
        v-for="user in activeUsers"
        :key="user.session_key"
        class="user-item"
      >
        <img
          :src="user.avatar || defaultAvatar"
          :alt="user.display_name"
          class="user-avatar"
        />
        <span class="user-name">{{ user.display_name }}さん</span>
        <span class="user-status" :class="{ online: true }">●</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from "vue";
import { storeToRefs } from "pinia";
import { useUsersStore } from "../stores/users";
import defaultAvatar from "@/assets/images/bust_in_silhouette.png";

const usersStore = useUsersStore();
const { activeUsers } = storeToRefs(usersStore);

// 定期的なユーザー更新
const UPDATE_INTERVAL = 30000; // 30秒
let updateInterval;

onMounted(() => {
  usersStore.fetchActiveUsers();
  updateInterval = setInterval(() => {
    usersStore.fetchActiveUsers();
  }, UPDATE_INTERVAL);
});

onUnmounted(() => {
  if (updateInterval) {
    clearInterval(updateInterval);
  }
});
</script>

<style scoped>
.user-list {
  background-color: #151520;
  color: white;
  padding: 1rem;
  height: 100vh;
  border-right: 1px solid #2d2d3f;
  width: 300px;
}

.user-list-header {
  padding-bottom: 1rem;
  border-bottom: 1px solid #2d2d3f;
}

.user-list-content {
  margin-top: 1rem;
}

.user-item {
  display: flex;
  align-items: center;
  padding: 0.8rem 0;
  border-bottom: 1px solid rgba(45, 45, 63, 0.5);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  margin-right: 0.8rem;
  object-fit: cover;
}

.user-name {
  flex-grow: 1;
  color: #e0e0e0;
}

.user-status {
  font-size: 0.8rem;
  color: #666;
}

.user-status.online {
  color: #4caf50;
}
</style>
