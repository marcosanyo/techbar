// frontend/src/composables/useWebSocket.js
import { ref } from "vue";

export function useWebSocket({ onMessage, onConnect, onDisconnect }) {
  const ws = ref(null);
  let reconnectAttempts = 0;
  const maxReconnectAttempts = 5;
  const reconnectDelay = 1000;

  function connect(url) {
    return new Promise((resolve, reject) => {
      try {
        console.log("Attempting to connect to WebSocket:", url);
        ws.value = new WebSocket(url);

        ws.value.onopen = () => {
          console.log("WebSocket connected successfully");
          reconnectAttempts = 0;
          onConnect?.();
          resolve();
        };

        ws.value.onmessage = (event) => {
          console.log("WebSocket message received:", event.data);
          onMessage?.(event.data);
        };

        ws.value.onclose = (event) => {
          console.log("WebSocket closed:", event.code, event.reason);
          onDisconnect?.();
          attemptReconnect(url);
        };

        ws.value.onerror = (error) => {
          console.error("WebSocket error:", error);
          reject(error);
        };
      } catch (error) {
        console.error("Failed to create WebSocket:", error);
        reject(error);
      }
    });
  }

  function attemptReconnect(url) {
    if (reconnectAttempts >= maxReconnectAttempts) {
      console.error("Max reconnection attempts reached");
      return;
    }

    reconnectAttempts++;
    console.log(
      `Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`
    );

    setTimeout(() => {
      connect(url).catch((error) => {
        console.error("Reconnection attempt failed:", error);
        attemptReconnect(url);
      });
    }, reconnectDelay * reconnectAttempts);
  }

  function sendMessage(message) {
    if (ws.value?.readyState === WebSocket.OPEN) {
      const messageStr =
        typeof message === "string" ? message : JSON.stringify(message);
      console.log("Sending WebSocket message:", messageStr);
      ws.value.send(messageStr);
    } else {
      console.error(
        "WebSocket is not connected. Current state:",
        ws.value?.readyState
      );
    }
  }

  return {
    connect,
    sendMessage,
  };
}
