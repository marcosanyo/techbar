// /frontend/src/main.js
import { createApp } from "vue";

// Vuetify
import "vuetify/styles";
import { createVuetify } from "vuetify";
import * as components from "vuetify/components";
import * as directives from "vuetify/directives";

// Pinia
import { createPinia } from "pinia";

// Components
import App from "./App.vue";

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: "dark",
    themes: {
      dark: {
        dark: true,
        colors: {
          primary: "#1e1e2e",
          secondary: "#2d2d3f",
          accent: "#4caf50",
          background: "#1e1e2e",
          surface: "#1e1e2e",
        },
      },
    },
  },
});

const pinia = createPinia();

createApp(App).use(vuetify).use(pinia).mount("#app");
