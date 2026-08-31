import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import * as React from "react"

import { cn } from "@/lib/utils"

/**
 * One press interaction for every button on every screen: nudge into the
 * shadow on hover, sit flush on the shadow when held. Variants change the
 * colour and nothing else - previously `default` hovered through a
 * rose/purple/blue gradient while `neutral` hovered through a cyan/emerald/lime
 * one, and the "Finish Match" button opted out of the border entirely.
 */
const buttonVariants = cva(
  [
    "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-base",
    "border-2 border-border font-heading",
    "transition-all duration-150",
    "shadow-shadow hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_var(--border)]",
    "active:translate-x-boxShadowX active:translate-y-boxShadowY active:shadow-none",
    "focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
    "disabled:pointer-events-none disabled:opacity-50",
    "[&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  ],
  {
    variants: {
      variant: {
        default: "bg-main text-main-foreground",
        neutral: "bg-secondary-background text-foreground",
        success: "bg-success text-main-foreground",
        danger: "bg-danger text-main-foreground",
        blue: "bg-blue-team text-main-foreground",
        red: "bg-red-team text-main-foreground",
        /** Flat - no shadow, no movement. For buttons inside an already
         *  raised surface, where a second shadow just adds noise. */
        noShadow:
          "bg-main text-main-foreground shadow-none hover:translate-x-0 hover:translate-y-0 hover:shadow-none active:translate-x-0 active:translate-y-0",
      },
      /* Pixelify Sans draws small for its point size - at 14px a "5" and an
         "8" are a couple of lit pixels apart, which is not a distinction to
         gamble on when someone is tapping "5 Bar" mid-rally. Every size is
         one step up from the equivalent sans size. */
      size: {
        default: "h-10 px-4 py-2 text-base",
        sm: "h-9 px-3 text-sm",
        lg: "h-11 px-8 text-lg",
        icon: "size-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean
  }) {
  const Comp = asChild ? Slot : "button"

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
