import { useState, useEffect, useCallback, useMemo } from "react";
import { analyticsApi } from "../api/analyticsApi";
import { accountApi } from "../../account/api/accountApi";
import { type ReportListItem } from "../types";
import { type UserStatus } from "../../account/types";
import { useAuth } from "../../../contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import { useTranslation } from "react-i18next";
import posthog from "posthog-js";

// Note: This custom hook demonstrates business logic separation, memoized client-side
// filtering/pagination, and local state updates to avoid unnecessary network refetches.

const ITEMS_PER_PAGE = 10;

export const useSidebarData = () => {
  const [fullHistory, setFullHistory] = useState<ReportListItem[]>([]);
  const [visibleCount, setVisibleCount] = useState(ITEMS_PER_PAGE);

  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [userStatus, setUserStatus] = useState<UserStatus | null>(null);
  const [isLoadingUserStatus, setIsLoadingUserStatus] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");

  const { t } = useTranslation();
  const navigate = useNavigate();
  const { logout } = useAuth();

  const loadUserStatus = useCallback(async () => {
    setIsLoadingUserStatus(true);
    try {
      const status = await accountApi.fetchStatus();
      setUserStatus(status);
    } catch (error) {
      console.error("Failed to load user status:", error);
    } finally {
      setIsLoadingUserStatus(false);
    }
  }, []);

  const loadHistory = useCallback(async (isInitialLoad = false) => {
    if (isInitialLoad) setIsLoadingHistory(true);
    try {
      const data = await analyticsApi.loadHistory();
      setFullHistory(data);
    } catch (error) {
      console.error("Failed to fetch user analytics history:", error);
    } finally {
      if (isInitialLoad) setIsLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    loadHistory(true);
    loadUserStatus();
  }, [loadHistory, loadUserStatus]);

  const filteredHistory = useMemo(() => {
    if (!searchQuery.trim()) return fullHistory;

    const query = searchQuery.toLowerCase();
    return fullHistory.filter((report) =>
      report.file_name.toLowerCase().includes(query),
    );
  }, [fullHistory, searchQuery]);

  // Client-side pagination
  const visibleHistory = useMemo(() => {
    return filteredHistory.slice(0, visibleCount);
  }, [filteredHistory, visibleCount]);

  const hasMoreHistory = visibleCount < filteredHistory.length;

  useEffect(() => {
    setVisibleCount(ITEMS_PER_PAGE);
  }, [searchQuery]);

  const loadMoreHistory = useCallback(() => {
    setVisibleCount((prev) => prev + ITEMS_PER_PAGE);
  }, []);

  const handleRenameReport = useCallback(
    async (id: number, newName: string, onSuccess?: () => void) => {
      try {
        await analyticsApi.renameReport(id, newName);

        // Update local state instead of triggering a full refetch
        setFullHistory((prev) =>
          prev.map((report) =>
            report.id === id ? { ...report, file_name: newName } : report,
          ),
        );

        if (onSuccess) onSuccess();
      } catch (err: unknown) {
        console.error("Failed to update report name:", err);
        posthog.capture("report_rename_failed", {
          report_id: id,
          error_message: err instanceof Error ? err.message : "Unknown error",
        });
        toast.error(t("sidebar.errors.renameFailed"));
      }
    },
    [t],
  );

  const handleDeleteReport = useCallback(
    async (id: number, onSuccess?: () => void) => {
      try {
        await analyticsApi.deleteReport(id);

        // Local state removal
        setFullHistory((prev) => prev.filter((report) => report.id !== id));

        if (onSuccess) onSuccess();
      } catch (err: unknown) {
        console.error("Failed to delete report:", err);
        posthog.capture("report_delete_failed", {
          report_id: id,
          error_message: err instanceof Error ? err.message : "Unknown error",
        });
        toast.error(t("sidebar.errors.deleteFailed"));
      }
    },
    [t],
  );

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return {
    history: visibleHistory,
    hasMoreHistory,
    loadMoreHistory,
    searchQuery,
    setSearchQuery,
    isLoadingHistory,
    isLoadingUserStatus,
    userStatus,
    loadHistory,
    loadUserStatus,
    handleRenameReport,
    handleDeleteReport,
    handleLogout,
  };
};
