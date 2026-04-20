import { createContext, useContext, useEffect, useState } from "react";

import { routeFromHash } from "../utils/appRuntime";

const AppStoreContext = createContext(null);

export function AppStoreProvider({ children }) {
  const [route, setRoute] = useState(routeFromHash());
  const [health, setHealth] = useState(null);
  const [status, setStatus] = useState("Ready to ingest a corpus or start chatting.");

  useEffect(() => {
    const onHashChange = () => setRoute(routeFromHash());
    window.addEventListener("hashchange", onHashChange);
    if (!window.location.hash) {
      window.location.hash = "#/chat";
    }
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  function navigate(nextRoute) {
    window.location.hash = nextRoute === "admin" ? "#/admin" : "#/chat";
  }

  const value = {
    route,
    navigate,
    health,
    setHealth,
    status,
    setStatus
  };

  return <AppStoreContext.Provider value={value}>{children}</AppStoreContext.Provider>;
}

export function useAppStore() {
  const value = useContext(AppStoreContext);
  if (!value) {
    throw new Error("useAppStore must be used within AppStoreProvider");
  }
  return value;
}
