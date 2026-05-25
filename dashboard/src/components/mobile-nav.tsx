"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Database, LayoutDashboard, Settings2 } from "lucide-react";

import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Workspace", icon: LayoutDashboard },
  { href: "/settings", label: "Config.", icon: Settings2 },
  { href: "/memory", label: "Memória", icon: Database },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-40 flex items-stretch h-16
        bg-bg-card border-t border-border"
      aria-label="Navegação principal"
    >
      {navItems.map(({ href, label, icon: Icon }) => {
        const isActive = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex flex-col items-center justify-center flex-1 gap-1 transition-colors duration-150",
              isActive
                ? "text-accent"
                : "text-text-muted active:text-text-secondary"
            )}
          >
            <Icon size={20} strokeWidth={isActive ? 2.5 : 1.75} />
            <span className="text-2xs font-medium">{label}</span>
            {isActive && (
              <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-0.5 rounded-full bg-accent" />
            )}
          </Link>
        );
      })}
    </nav>
  );
}
