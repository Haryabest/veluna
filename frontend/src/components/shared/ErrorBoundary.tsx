"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { useTranslation } from "@/hooks/use-translation";
import { Button } from "./Button";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
}

function ErrorBoundaryFallback({ onRetry }: { onRetry: () => void }) {
  const { t } = useTranslation();

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-6">
      <p className="text-center text-text-secondary">{t("error.somethingWrong")}</p>
      <Button onClick={onRetry} variant="secondary">
        {t("common.retry")}
      </Button>
    </div>
  );
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <ErrorBoundaryFallback onRetry={() => this.setState({ hasError: false })} />
        )
      );
    }
    return this.props.children;
  }
}
