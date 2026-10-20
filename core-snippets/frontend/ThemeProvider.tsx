import React, { createContext, useContext, useEffect, useState } from "react";

// Note: This snippet demonstrates an enterprise-grade Theme Provider for Brio AI featuring
// centralized theme options, system preference media queries, cross-tab synchronization via
// Storage events, dynamic SVG favicon swapping, and browser chrome tinting.

export type Theme = "light" | "dark" | "system";

export interface ThemeOption {
  value: Theme;
  labelKey: string;
}

// Centralized options shared across settings panels, footer dropdowns, and toggles
export const THEME_OPTIONS: ThemeOption[] = [
  { value: "light", labelKey: "settings.themeOptions.lightTheme" },
  { value: "dark", labelKey: "settings.themeOptions.darkTheme" },
  { value: "system", labelKey: "settings.themeOptions.autoTheme" },
];

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: Theme;
}

interface ThemeProviderState {
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

const ThemeProviderContext = createContext<ThemeProviderState | undefined>(
  undefined,
);

/**
 * iOS Safari ignores dynamic <meta name="theme-color"> changes on class toggles.
 * Briefly mounting a hidden fixed probe forces Safari's compositor to resample the top-edge
 * color immediately so status bar and notch tinting blend seamlessly.
 */
const forceSafariChromeResample = () => {
  const probe = document.createElement("div");
  probe.setAttribute("aria-hidden", "true");
  probe.style.cssText =
    "position:fixed;inset:0;pointer-events:none;z-index:2147483647;background:rgba(0,0,0,0.01);";
  document.body.appendChild(probe);

  requestAnimationFrame(() => {
    requestAnimationFrame(() => probe.remove());
  });
};

export function ThemeProvider({
  children,
  defaultTheme = "system",
}: ThemeProviderProps) {
  const [theme, setTheme] = useState<Theme>(() => {
    return (localStorage.getItem("ui-theme") as Theme) || defaultTheme;
  });

  // Handle DOM updates, dynamic favicons, meta tags, and system preference listeners
  useEffect(() => {
    const root = window.document.documentElement;

    const applyTheme = () => {
      root.classList.remove("light", "dark");

      const resolvedTheme =
        theme === "system"
          ? window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light"
          : theme;

      root.classList.add(resolvedTheme);
      root.style.colorScheme = resolvedTheme;

      // Keep browser chrome (status bar / navigation tint) synchronized
      const themeColor = resolvedTheme === "dark" ? "#07080A" : "#ffffff";
      const oldMeta = document.querySelector('meta[name="theme-color"]');
      const newMeta = document.createElement("meta");
      newMeta.name = "theme-color";
      newMeta.content = themeColor;
      if (oldMeta) oldMeta.replaceWith(newMeta);
      else document.head.appendChild(newMeta);

      // Dynamic favicon swapping for seamless OS-level integration
      const favicon = document.getElementById("app-favicon") as HTMLLinkElement;
      if (favicon) {
        favicon.href =
          resolvedTheme === "dark" ? "/favicon-dark.svg" : "/favicon-light.svg";
      }
    };

    applyTheme();
    forceSafariChromeResample();
    localStorage.setItem("ui-theme", theme);

    if (theme === "system") {
      const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
      const handleChange = () => {
        applyTheme();
        forceSafariChromeResample();
      };

      mediaQuery.addEventListener("change", handleChange);
      return () => mediaQuery.removeEventListener("change", handleChange);
    }
  }, [theme]);

  // Cross-tab synchronization via Storage events
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "ui-theme" && e.newValue) {
        setTheme(e.newValue as Theme);
      }
    };

    window.addEventListener("storage", handleStorageChange);
    return () => window.removeEventListener("storage", handleStorageChange);
  }, []);

  const value = {
    theme,
    setTheme: (newTheme: Theme) => {
      localStorage.setItem("ui-theme", newTheme);
      setTheme(newTheme);
    },
  };

  return (
    <ThemeProviderContext.Provider value={value}>
      {children}
    </ThemeProviderContext.Provider>
  );
}

// Custom Hook to consume theme state in any component
export const useTheme = () => {
  const context = useContext(ThemeProviderContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
};
