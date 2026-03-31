import { createApp } from "vue";
import { createPinia } from "pinia";
import "./styles/main.css";
import App from "./App.vue";
import router from "./router";
import { useAuthStore } from "./stores/auth";

const app = createApp(App);
const pinia = createPinia();
const auth = useAuthStore(pinia);

type SpotlightElement = HTMLElement & {
  __spotlightMove__?: (event: PointerEvent) => void;
  __spotlightLeave__?: () => void;
};

app.directive("spotlight", {
  mounted(el: SpotlightElement) {
    const updateSpotlight = (event: PointerEvent) => {
      const bounds = el.getBoundingClientRect();
      const x = ((event.clientX - bounds.left) / bounds.width) * 100;
      const y = ((event.clientY - bounds.top) / bounds.height) * 100;
      el.style.setProperty("--spotlight-x", `${x}%`);
      el.style.setProperty("--spotlight-y", `${y}%`);
    };

    const resetSpotlight = () => {
      el.style.setProperty("--spotlight-x", "50%");
      el.style.setProperty("--spotlight-y", "50%");
    };

    el.classList.add("interactive-spotlight");
    resetSpotlight();
    el.__spotlightMove__ = updateSpotlight;
    el.__spotlightLeave__ = resetSpotlight;
    el.addEventListener("pointermove", updateSpotlight);
    el.addEventListener("pointerleave", resetSpotlight);
  },
  beforeUnmount(el: SpotlightElement) {
    if (el.__spotlightMove__) {
      el.removeEventListener("pointermove", el.__spotlightMove__);
    }
    if (el.__spotlightLeave__) {
      el.removeEventListener("pointerleave", el.__spotlightLeave__);
    }
  },
});

async function bootstrap() {
  app.use(pinia);
  if (localStorage.getItem("access_token")) {
    await auth.fetchMe().catch(() => {
      auth.clearAuth();
    });
  }

  app.use(router);
  if (!auth.isAuthenticated && router.currentRoute.value.path !== "/login") {
    await router.replace("/login");
  }
  await router.isReady();
  app.mount("#app");
}

void bootstrap();
