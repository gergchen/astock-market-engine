import * as React from "react"
import { cn } from "@/lib/utils"

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "up" | "down"
}

const badgeVariants = {
  default: "bg-primary/10 text-primary border-primary/15",
  secondary: "bg-white/[0.04] text-white/40 border-white/[0.06]",
  destructive: "bg-rose-500/10 text-rose-400 border-rose-500/15",
  outline: "border border-white/[0.06] text-white/30",
  up: "bg-up-subtle text-up",
  down: "bg-down-subtle text-down",
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-medium tracking-wider",
        badgeVariants[variant],
        className
      )}
      {...props}
    />
  )
}

export { Badge }
