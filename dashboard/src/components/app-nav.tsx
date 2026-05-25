"use client";

import { Database, LayoutDashboard, Settings2 } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Workspace", icon: LayoutDashboard },
  { href: "/settings", label: "Configurações", icon: Settings2 },
  { href: "/memory", label: "Memória", icon: Database },
];

export function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="space-y-1" aria-label="Principal">
      {navItems.map(({ href, label, icon: Icon }) => {
        const isActive = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 border",
              isActive
                ? "bg-accent/10 text-accent border-accent/20"
                : "text-text-secondary hover:text-text-primary hover:bg-bg-hover border-transparent"
            )}
          >
            <Icon size={16} className={cn(isActive ? "text-accent" : "text-text-muted")} />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}
