"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Workspace" },
  { href: "/settings", label: "Settings" },
  { href: "/memory", label: "Memory" },
];

export function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="rail-nav" aria-label="Primary">
      {navItems.map((item) => (
        <Link
          key={item.href}
          className={`nav-item ${pathname === item.href ? "current" : ""}`}
          href={item.href}
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
