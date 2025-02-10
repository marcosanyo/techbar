<!-- frontend/src/components/UserNameInput.vue -->
<template>
  <div class="name-input-overlay">
    <div class="name-input-container">
      <v-card class="name-input-card">
        <v-card-title class="text-h4 mb-2 d-flex align-center">
          🌃 深夜のテックバー🌙
        </v-card-title>
        <v-card-subtitle class="text-h6">
          🚪 いらっしゃいませ！
        </v-card-subtitle>
        <v-card-text>
          <v-container>
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="userName"
                  label="ニックネームを入力してください"
                  required
                  :error-messages="errorMessage"
                  @keyup.enter="submit"
                  variant="outlined"
                  bg-color="background"
                  :disabled="isSubmitting"
                ></v-text-field>
              </v-col>
            </v-row>
          </v-container>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            @click="submit"
            :disabled="!userName.trim() || isSubmitting"
            :loading="isSubmitting"
            class="px-6"
          >
            {{ isSubmitting ? "入店中..." : "入店する" }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const userName = ref("");
const errorMessage = ref("");
const isSubmitting = ref(false);

// eslint-disable-next-line
const emit = defineEmits(["submit"]);

const submit = async () => {
  if (isSubmitting.value) return;

  if (!userName.value.trim()) {
    errorMessage.value = "お名前を入力してください";
    return;
  }

  try {
    isSubmitting.value = true;
    emit("submit", userName.value.trim());
  } catch (error) {
    console.error("Submit error:", error);
    errorMessage.value = "エラーが発生しました。もう一度お試しください。";
  } finally {
    setTimeout(() => {
      isSubmitting.value = false;
    }, 3000);
  }
};
</script>

<style scoped>
.name-input-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(30, 30, 46, 0.95);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.name-input-container {
  width: 100%;
  max-width: 500px;
  padding: 20px;
  margin: 0 auto;
}

.name-input-card {
  background-color: #1a1a2e !important;
  border: 1px solid #2d2d3f;
}

:deep(.v-card-title) {
  color: #ffffff;
}

:deep(.v-label) {
  color: #ffffff !important;
}

:deep(.v-field) {
  color: #ffffff !important;
  border-color: #2d2d3f !important;
}

.welcome-icon {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

:deep(.v-btn) {
  color: white !important;
  background-color: #4caf50 !important;
  margin-bottom: 16px;
}

/* モバイル対応のスタイル */
@media (max-width: 600px) {
  .name-input-container {
    padding: 16px;
    width: 90%;
  }

  .name-input-card {
    margin: 0 auto;
  }

  :deep(.v-card-title) {
    font-size: 1.5rem !important;
    text-align: center;
  }

  :deep(.v-card-subtitle) {
    font-size: 1.1rem !important;
    text-align: center;
  }

  :deep(.v-card-actions) {
    justify-content: center;
  }

  :deep(.v-btn) {
    width: 100%;
    margin-bottom: 8px;
  }
}
</style>
