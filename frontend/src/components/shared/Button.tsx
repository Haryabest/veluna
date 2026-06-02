import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
}

const variants = {
  primary: "bg-accent hover:bg-accent/90 text-white glow-accent",
  secondary: "bg-bg-elevated hover:bg-bg-card text-text-primary border border-border",
  ghost: "hover:bg-bg-elevated text-text-secondary",
  danger: "bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30",
};

const sizes = {
  sm: "px-3 py-1.5 text-sm rounded-sm",
  md: "px-4 py-2.5 text-sm rounded-md",
  lg: "px-6 py-3 text-base rounded-lg",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", loading, disabled, children, ...props }, ref) => (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center font-medium transition-all duration-200",
        "disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]",
        variants[variant],
        sizes[size],
        className
      )}
      {...props}
    >
      {loading ? (
        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
      ) : null}
      {children}
    </button>
  )
);
Button.displayName = "Button";
