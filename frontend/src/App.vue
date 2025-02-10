<!-- frontend/src/App.vue -->
<template>
  <v-app theme="dark">
    <v-container class="pa-0 fill-height" fluid>
      <v-row no-gutters class="fill-height">
        <!-- お客様欄: 左側に配置 -->
        <v-navigation-drawer
          v-model="showUserList"
          :permanent="!isMobile"
          :temporary="isMobile"
          :width="300"
          location="left"
        >
          <UserList />
        </v-navigation-drawer>

        <!-- メインコンテンツエリア -->
        <v-col>
          <!-- モバイル用のヘッダー -->
          <v-app-bar v-if="isMobile" density="compact">
            <v-app-bar-nav-icon @click="toggleUserList" color="primary" />
            <v-app-bar-title class="text-center">
              深夜のテックバー
            </v-app-bar-title>
          </v-app-bar>

          <!-- チャットエリア -->
          <v-main :class="{ 'has-mobile-header': isMobile }">
            <ChatRoom />
          </v-main>
        </v-col>
      </v-row>
    </v-container>
  </v-app>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";
import ChatRoom from "./components/ChatRoom.vue";
import UserList from "./components/UserList.vue";

// モバイルビューの状態管理
const showUserList = ref(!isMobileDevice());
const isMobile = ref(false);

function isMobileDevice() {
  return window.innerWidth < 960;
}

// ウィンドウサイズの監視
const checkMobile = () => {
  const wasMobile = isMobile.value;
  isMobile.value = isMobileDevice();

  // PCからモバイルに切り替わった時
  if (!wasMobile && isMobile.value) {
    showUserList.value = false;
  }
  // モバイルからPCに切り替わった時
  else if (wasMobile && !isMobile.value) {
    showUserList.value = true;
  }
};

// ユーザーリストの表示切り替え
const toggleUserList = () => {
  showUserList.value = !showUserList.value;
};

onMounted(() => {
  checkMobile();
  window.addEventListener("resize", checkMobile);
});

onUnmounted(() => {
  window.removeEventListener("resize", checkMobile);
});
</script>

<style>
:root {
  --app-background: #1e1e2e;
  --header-height: 48px;
}

.v-application {
  background-color: var(--app-background) !important;
}

.has-mobile-header {
  padding-top: var(--header-height);
}

@media (min-width: 960px) {
  .v-navigation-drawer {
    transform: translateX(0) !important;
  }
}
</style>
