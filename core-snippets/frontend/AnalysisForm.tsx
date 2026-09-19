import React, { useState, useRef } from "react";
import { FaCheckSquare, FaShieldAlt } from "react-icons/fa";
import { TbDragDrop } from "react-icons/tb";
import monoLogo from "../../../assets/banks/monobank_logo.svg";
import privatLogo from "../../../assets/banks/privatbank_logo.svg";
import raifLogo from "../../../assets/banks/raiffeisenbank_logo.svg";
import { BankInstructionModal } from "./BankInstructionModal";
import { useTranslation, Trans } from "react-i18next";
import posthog from "posthog-js";

// Note: This snippet highlights the drag-and-drop file upload interface,
// event-driven PostHog analytics tracking, and dynamic Tailwind styling in Brio AI.

interface AnalysisFormProps {
  onAnalyzePipeline: (file: File, userGoal: string) => Promise<boolean>;
  isSubmitting: boolean;
}

type BankId = "monobank" | "privatbank" | "raiffeisen";

interface SupportedBank {
  id: BankId;
  name: string;
  icon: React.ReactNode;
}

const MAX_FILE_SIZE = 2 * 1024 * 1024; // 2MB

const SUPPORTED_BANKS: SupportedBank[] = [
  {
    id: "monobank",
    name: "Monobank",
    icon: (
      <img
        src={monoLogo}
        alt="Monobank"
        className="w-10 h-10 rounded-xl object-contain transition-all duration-300 group-hover:scale-110 group-hover:-translate-y-1 group-hover:drop-shadow-[0_6px_8px_rgba(145,145,148,0.4)]"
      />
    ),
  },
  {
    id: "privatbank",
    name: "PrivatBank",
    icon: (
      <img
        src={privatLogo}
        alt="PrivatBank"
        className="w-10 h-10 rounded-xl object-contain bg-[#DCF3D5] transition-all duration-300 group-hover:scale-110 group-hover:-translate-y-1 group-hover:drop-shadow-[0_6px_8px_rgba(115,181,20,0.4)]"
      />
    ),
  },
  {
    id: "raiffeisen",
    name: "Raiffeisen Bank",
    icon: (
      <img
        src={raifLogo}
        alt="RaiffeisenBank"
        className="w-10 h-10 rounded-full object-contain transition-all duration-300 group-hover:scale-110 group-hover:-translate-y-1 group-hover:drop-shadow-[0_6px_8px_rgba(232,232,16,0.4)]"
      />
    ),
  },
];

export const AnalysisForm: React.FC<AnalysisFormProps> = ({
  onAnalyzePipeline,
  isSubmitting,
}) => {
  const [userGoal, setUserGoal] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const [instructionBankId, setInstructionBankId] = useState<BankId | null>(
    null,
  );

  const fileInputRef = useRef<HTMLInputElement>(null);
  const { t } = useTranslation();

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    setLocalError(null);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (
        droppedFile.name.endsWith(".csv") ||
        droppedFile.name.endsWith(".xlsx")
      ) {
        setFile(droppedFile);
      } else {
        setLocalError(t("analysisForm.errorUnsupportedFormat"));
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setLocalError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!file) return;

    if (file.size > MAX_FILE_SIZE) {
      setLocalError(t("analysisForm.errorFileSize"));
      setFile(null);
      return;
    }

    const isSuccess = await onAnalyzePipeline(file, userGoal);
    if (isSuccess) {
      posthog.capture("report_analyzed_successfully", {
        has_custom_goal: userGoal.trim().length > 0,
        file_type: file.name.split(".").pop(),
      });

      setUserGoal("");
      setFile(null);
    }
  };

  return (
    <div className="max-w-3xl mx-auto mt-6 transition-colors duration-300 animate-fadeIn">
      <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
        {t("analysisForm.title")}
      </h2>
      <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
        {t("analysisForm.subtitle")}
      </p>

      {localError && (
        <div className="p-4 mt-6 text-sm text-red-600 border border-red-200 rounded-xl bg-red-50 dark:bg-red-500/10 dark:border-red-500/20 dark:text-red-400">
          {localError}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-10 space-y-6">
        {/* Drag and Drop Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300 ${
            isDragging
              ? "border-emerald-400 bg-emerald-50 dark:bg-emerald-500/5 shadow-[0_0_30px_rgba(16,185,129,0.1)]"
              : file
                ? "bg-emerald-50/50 border-emerald-300 dark:border-emerald-500/40 dark:bg-emerald-500/5"
                : "bg-white hover:border-emerald-400 hover:bg-emerald-50/30 border-gray-200 dark:border-white/10 dark:hover:border-emerald-500/30 dark:hover:bg-white/10 dark:bg-white/5"
          }`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept=".csv, .xlsx"
            className="hidden"
          />
          <div className="flex flex-col items-center justify-center">
            <span className="mb-3">
              {file ? (
                <FaCheckSquare className="text-emerald-500/90" size={24} />
              ) : (
                <TbDragDrop
                  className="text-gray-400 dark:text-gray-400/60"
                  size={28}
                />
              )}
            </span>
            {file ? (
              <div>
                <p className="text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                  {file.name}
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  {t("analysisForm.fileStaged", {
                    size: (file.size / 1024).toFixed(2),
                  })}
                </p>
              </div>
            ) : (
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300">
                  <Trans
                    i18nKey="analysisForm.dragDrop"
                    components={{
                      1: (
                        <span className="font-semibold text-emerald-500 dark:text-emerald-400 hover:underline" />
                      ),
                    }}
                  />
                </p>
                <p className="mt-2 text-xs text-gray-400 dark:text-gray-600">
                  {t("analysisForm.supportsFormats")}
                </p>
                <p className="mt-2 text-xs italic text-gray-400 dark:text-gray-600">
                  {t("analysisForm.limitsHint")}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Security & Privacy Disclaimer */}
        <div className="flex items-start gap-3 p-4 bg-gray-50 border border-gray-200 rounded-xl dark:bg-white/5 dark:border-white/10">
          <FaShieldAlt className="text-emerald-500 shrink-0 mt-0.5" size={16} />
          <div className="flex flex-col gap-1">
            <p className="text-xs font-medium text-gray-700 dark:text-gray-300">
              {t("analysisForm.privacyTitle")}
            </p>
            <p className="text-[11px] leading-relaxed text-gray-500 dark:text-gray-400">
              <Trans
                i18nKey="analysisForm.privacyText"
                components={{
                  1: (
                    <span className="font-semibold text-gray-700 dark:text-gray-300" />
                  ),
                }}
              />
            </p>
          </div>
        </div>

        {/* User Goal */}
        <div className="flex flex-col gap-2">
          <label className="px-1 text-xs font-bold tracking-wide text-gray-500 uppercase dark:text-gray-400">
            {t("analysisForm.goalLabel")}
          </label>
          <textarea
            value={userGoal}
            onChange={(e) => setUserGoal(e.target.value)}
            placeholder={t("analysisForm.userGoalPlaceholder")}
            className="w-full h-32 rounded-2xl border border-gray-200 bg-white dark:border-white/6 dark:bg-[#0D0E12]/80 p-4 text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 dark:focus:border-emerald-500/40 transition-all resize-none shadow-sm dark:shadow-none"
          />
        </div>

        {/* Supported banks block */}
        <div className="flex flex-col items-center mt-8 mb-4">
          <p className="mb-4 text-xs font-bold tracking-wider text-gray-500 uppercase dark:text-gray-500">
            {t("analysisForm.howToDownload")}
          </p>
          <div className="flex items-center gap-4">
            {SUPPORTED_BANKS.map((bank) => (
              <div
                key={bank.id}
                className="flex flex-col items-center cursor-pointer group"
                onClick={() => setInstructionBankId(bank.id)}
              >
                {bank.icon}
              </div>
            ))}
          </div>
        </div>

        {/* Language info badge */}
        <div className="flex items-center justify-center gap-2 px-1 pt-2 mb-4">
          <div className="relative flex w-2 h-2">
            <span className="absolute inline-flex w-full h-full bg-indigo-400 rounded-full opacity-75 animate-ping"></span>
            <span className="relative inline-flex w-2 h-2 rounded-full bg-emerald-500"></span>
          </div>
          <span className="text-xs font-semibold text-gray-500 dark:text-gray-400">
            {t("analysisForm.languageInfo")}
          </span>
        </div>

        <button
          type="submit"
          disabled={isSubmitting || !file}
          className={`w-full py-4 rounded-2xl font-bold text-sm text-center tracking-wide transition-all duration-200 ${
            !file
              ? "bg-gray-100 text-gray-400 border-gray-200 dark:bg-white/2 dark:text-gray-600 border dark:border-white/5 cursor-not-allowed"
              : isSubmitting
                ? "bg-emerald-50 text-emerald-600 border-emerald-200 dark:bg-emerald-500/20 dark:text-emerald-400 border dark:border-emerald-500/30 animate-pulse cursor-wait"
                : "bg-emerald-500 text-white dark:text-[#07080A] hover:bg-emerald-600 dark:hover:bg-emerald-400 shadow-md hover:shadow-lg dark:shadow-[0_0_25px_rgba(16,185,129,0.2)] active:scale-99"
          }`}
        >
          {isSubmitting
            ? t("analysisForm.executing")
            : t("analysisForm.analyzeBtn")}
        </button>
      </form>
      <BankInstructionModal
        bankId={instructionBankId}
        onClose={() => setInstructionBankId(null)}
      />
    </div>
  );
};
