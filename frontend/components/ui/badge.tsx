import * as React from "react"
import { cn } from "@/lib/utils"

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "destructive" | "outline" | "up" | "down"
}

const badgeVariants = {
  default: "bg-primary/12 text-primary border-primary/20",
  secondary: "bg-secondary text-secondary-foreground",
  destructive: "bg-destructive/12 text-destructive border-destructive/20",
  outline: "border border-border text-muted-foreground",
  up: "bg-up-subtle text-up",
  down: "bg-down-subtle text-down",
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded border px-2 py-0.5 text-[11px] font-medium tracking-wide",
        badgeVariants[variant],
        className
      )}
      {...props}
    />
  )
}

export { Badge }
