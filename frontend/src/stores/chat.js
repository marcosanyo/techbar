// frontend/src/stores/chat.js
import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { useWebSocket } from "../composables/useWebSocket";
import { useUsersStore } from "./users";
import masterAvatar from "@/assets/images/sparkles.png";
import { getAvatarForUser } from "../utils/avatar";

const API_BASE_URL = "";

export const useChatStore = defineStore("chat", () => {
  const messages = ref([]);
  const isConnected = ref(false);
  const currentRoomId = ref("general");
  const sessionKey = ref("");
  const displayName = ref("");
  const messageCount = ref(0);
  const usersStore = useUsersStore();

  // WebSocket処理
  const handleWebSocketMessage = (data) => {
    try {
      console.log("Received WebSocket data:", data);
      const message = JSON.parse(data);
      console.log("Parsed WebSocket message:", message);

      let messageToAdd = null;

      // 1. まずシステムメッセージかどうかを判定
      if (message.system === true) {
        messageToAdd = {
          _id: message.message_id || crypto.randomUUID(),
          content: message.content,
          senderId: "system",
          username: "system",
          // timestamp: message.timestamp,
          system: true,
          disableActions: true,
          disableReactions: true,
        };
      }
      // 2. マスターの入店時歓迎メッセージの場合は特別にシステムメッセージとして扱う
      else if (
        message.display_name === "マスター" &&
        message.content.includes("ごゆっくりおくつろぎください。")
      ) {
        messageToAdd = {
          _id: message.message_id || crypto.randomUUID(),
          content: message.content,
          senderId: "system",
          username: "system",
          // timestamp: message.timestamp,
          system: true,
          disableActions: true,
          disableReactions: true,
        };
      }
      // 3. 通常のマスターメッセージを判定
      else if (message.display_name === "マスター") {
        messageToAdd = {
          _id: message.message_id || crypto.randomUUID(),
          content: message.content,
          senderId: "master",
          username: "マスター",
          // timestamp: message.timestamp,
          system: false,
          avatar: masterAvatar,
        };
      }
      // 4. 最後に通常のユーザーメッセージを判定
      else if (
        message.type === "message" &&
        message.display_name !== displayName.value
      ) {
        messageToAdd = {
          _id: message.message_id || crypto.randomUUID(),
          content: message.content,
          senderId: message.display_name,
          username: message.display_name,
          // timestamp: message.timestamp,
          system: false,
          avatar: getAvatarForUser(message.display_name),
        };
      }

      // メッセージが作成された場合のみ追加
      if (messageToAdd) {
        console.log("Adding message:", messageToAdd);
        messages.value.push(messageToAdd);
      }
    } catch (error) {
      console.error("Error handling WebSocket message:", error);
    }
  };

  const { connect: wsConnect, sendMessage: wsMessage } = useWebSocket({
    onMessage: handleWebSocketMessage,
    onConnect: () => {
      console.log("WebSocket connected");
      isConnected.value = true;
    },
    onDisconnect: () => {
      console.log("WebSocket disconnected");
      isConnected.value = false;
    },
  });

  // バーに入店（セッション開始）
  const enterBar = async (name) => {
    console.log("enterBar started with name:", name);
    try {
      const newSessionKey = crypto.randomUUID();
      console.log("Generated session key:", newSessionKey);

      console.log("Sending enter request to API...");
      const response = await fetch(`${API_BASE_URL}/api/users/enter`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_key: newSessionKey,
          display_name: name,
        }),
      });

      console.log("API response status:", response.status);
      if (!response.ok) {
        const errorData = await response.json();
        console.error("API error response:", errorData);
        throw new Error(errorData.detail || "Failed to enter bar");
      }

      const data = await response.json();
      console.log("API response data:", data);

      sessionKey.value = newSessionKey;
      displayName.value = name;

      // セッション確立後にWebSocket接続を開始
      const wsUrl = `${API_BASE_URL.replace("http", "ws")}/ws/${newSessionKey}`;
      console.log("Attempting WebSocket connection to:", wsUrl);

      try {
        await wsConnect(wsUrl);
        console.log("WebSocket connection established");
        isConnected.value = true;

        // WebSocket接続成功後に初期化メッセージを送信
        setTimeout(() => {
          wsMessage({
            type: "welcome",
            session_key: newSessionKey,
            display_name: name,
          });
        }, 1000); // 1秒後に初期化メッセージを送信

        return true;
      } catch (wsError) {
        console.error("WebSocket connection failed:", wsError);
        throw new Error("WebSocket connection failed");
      }
    } catch (error) {
      console.error("Error in enterBar:", error);
      isConnected.value = false;
      throw error;
    }
  };

  const sendMessage = async (content) => {
    let messageId;
    try {
      if (!content) {
        throw new Error("メッセージの内容が空です");
      }

      if (!sessionKey.value || !displayName.value) {
        throw new Error("セッションが初期化されていません");
      }

      const trimmedContent = content.trim();
      if (!trimmedContent) {
        throw new Error("メッセージの内容が空です");
      }

      messageCount.value++;
      messageId = `msg_${messageCount.value}`;
      const currentTimestamp = new Date().toISOString();

      const userAvatar = getAvatarForUser(displayName.value);

      // 自分のメッセージをローカルに追加
      const myMessage = {
        _id: messageId,
        content: trimmedContent,
        senderId: displayName.value,
        username: displayName.value,
        timestamp: currentTimestamp,
        system: false,
        status: "sending",
        avatar: userAvatar,
      };
      console.log("Adding own message:", myMessage);
      messages.value.push(myMessage);

      // API リクエストの送信
      const response = await fetch(`${API_BASE_URL}/api/chat/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          content: trimmedContent,
          type: "user",
          session_key: sessionKey.value,
          display_name: displayName.value,
          message_id: messageId,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Error response:", errorData);
        throw new Error(errorData.detail || "メッセージの送信に失敗しました");
      }

      const data = await response.json();

      // メッセージのステータスを更新
      const msgIndex = messages.value.findIndex((m) => m._id === messageId);
      if (msgIndex !== -1) {
        messages.value[msgIndex].status = "sent";
        messages.value[msgIndex].timestamp = currentTimestamp;
      }

      // WebSocketを通じてメッセージを送信
      wsMessage({
        type: "user_message",
        content: trimmedContent,
        display_name: displayName.value,
        message_id: messageId,
        timestamp: currentTimestamp,
      });

      return data;
    } catch (error) {
      console.error("Error sending message:", error);
      // メッセージのステータスをエラーに更新
      const msgIndex = messages.value.findIndex((m) => m._id === messageId);
      if (msgIndex !== -1) {
        messages.value[msgIndex].status = "error";
      }
      throw error;
    }
  };

  // アクティブユーザーの更新
  const updateActiveUsers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/users/active`);
      if (!response.ok) throw new Error("Failed to fetch active users");

      const data = await response.json();
      usersStore.updateUsers(data.users);
    } catch (error) {
      console.error("Error updating active users:", error);
    }
  };

  // 定期的な更新処理の管理
  let updateInterval;
  const startPeriodicUpdates = () => {
    updateInterval = setInterval(updateActiveUsers, 30000);
  };

  const stopPeriodicUpdates = () => {
    if (updateInterval) {
      clearInterval(updateInterval);
    }
  };

  // メッセージソート用のComputed
  const sortedMessages = computed(() => {
    return [...messages.value].sort((a, b) => {
      const timeA = new Date(a.timestamp).getTime();
      const timeB = new Date(b.timestamp).getTime();
      return timeA - timeB;
    });
  });

  return {
    messages: sortedMessages,
    isConnected,
    currentRoomId,
    sessionKey,
    displayName,
    sendMessage,
    enterBar,
    startPeriodicUpdates,
    stopPeriodicUpdates,
  };
});
