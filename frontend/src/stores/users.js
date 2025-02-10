// frontend/src/stores/users.js
import { defineStore } from "pinia";
import { ref } from "vue";
import masterAvatar from "@/assets/images/sparkles.png";

// UserAvatarディレクトリから全アバター画像をインポート
const avatarContext = require.context(
  "@/assets/images/UserAvatar",
  false,
  /\.(png|jpg|jpeg|svg)$/
);
const avatarImages = avatarContext.keys().map((key) => avatarContext(key));

// frontend/src/stores/users.js
const API_BASE_URL = "";

// ユーザー名からアバターを決定する関数
function getAvatarForUser(username) {
  if (!username) return avatarImages[0];

  // ユーザー名を文字コードの合計値に変換してシード値とする
  const seed = username
    .split("")
    .reduce((acc, char) => acc + char.charCodeAt(0), 0);

  // シード値を使用してアバターをランダムに選択
  return avatarImages[seed % avatarImages.length];
}

export const useUsersStore = defineStore("users", () => {
  const activeUsers = ref([
    {
      session_key: "master",
      display_name: "マスター",
      avatar: masterAvatar,
      is_master: true,
    },
  ]);

  const fetchActiveUsers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/users/active`);
      if (!response.ok) throw new Error("Failed to fetch active users");

      const data = await response.json();
      updateUsers(data.users);
    } catch (error) {
      console.error("Error fetching active users:", error);
    }
  };

  const updateUsers = (users) => {
    activeUsers.value = [
      {
        session_key: "master",
        display_name: "マスター",
        avatar: masterAvatar,
        is_master: true,
      },
      ...users.map((user) => ({
        session_key: user.session_key,
        display_name: user.display_name,
        avatar: getAvatarForUser(user.display_name),
        last_active: user.last_active,
      })),
    ];
  };

  return {
    activeUsers,
    fetchActiveUsers,
    updateUsers,
  };
});
