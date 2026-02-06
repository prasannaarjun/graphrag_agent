import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { Slot } from "radix-ui"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center justify-center rounded-full border border-transparent px-3 py-1 text-xs font-medium font-body w-fit whitespace-nowrap shrink-0 [&>svg]:size-3 gap-1.5 [&>svg]:pointer-events-none focus-visible:border-accent focus-visible:ring-2 focus-visible:ring-accent/20 aria-invalid:ring-2 aria-invalid:ring-destructive/20 aria-invalid:border-destructive transition-refined overflow-hidden",
  {
    variants: {
      variant: {
        default: "bg-accent text-primary-foreground shadow-refined-sm [a&]:hover:bg-accent-hover",
        secondary:
          "bg-secondary text-secondary-foreground shadow-refined-sm [a&]:hover:bg-secondary/80",
        destructive:
          "bg-destructive text-white shadow-refined-sm [a&]:hover:opacity-90 focus-visible:ring-destructive/20",
        outline:
          "border-border text-fg bg-card shadow-refined-sm [a&]:hover:bg-accent-subtle [a&]:hover:border-accent",
        success:
          "bg-success text-white shadow-refined-sm [a&]:hover:opacity-90",
        ghost: "[a&]:hover:bg-accent-subtle [a&]:hover:text-accent",
        link: "text-accent underline-offset-4 [a&]:hover:underline",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

function Badge({
  className,
  variant = "default",
  asChild = false,
  ...props
}: React.ComponentProps<"span"> &
  VariantProps<typeof badgeVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot.Root : "span"

  return (
    <Comp
      data-slot="badge"
      data-variant={variant}
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  )
}

export { Badge, badgeVariants }
