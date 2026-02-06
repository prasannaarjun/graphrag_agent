"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
    LayoutDashboard,
    MessageSquare,
    Database,
    Settings,
} from "lucide-react";

const navItems = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/chat", label: "Chat", icon: MessageSquare },
    { href: "/kb", label: "Knowledge Base", icon: Database },
    { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="hidden w-72 flex-shrink-0 border-r border-border/50 bg-card lg:block">
            {/* Logo / Brand */}
            <div className="flex h-20 items-center px-8 border-b border-border/50">
                <Link
                    href="/dashboard"
                    className="flex items-center gap-3 group transition-refined"
                >
                    {/* Refined brand icon */}
                    <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-accent to-accent-hover flex items-center justify-center shadow-refined-sm group-hover:shadow-refined-md transition-refined">
                        <svg
                            className="h-6 w-6 text-primary-foreground"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            {/* Elegant graph icon */}
                            <circle cx="18" cy="5" r="3" />
                            <circle cx="6" cy="12" r="3" />
                            <circle cx="18" cy="19" r="3" />
                            <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
                            <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
                        </svg>
                    </div>
                    <span className="font-display text-2xl font-semibold text-fg tracking-tight">
                        GraphRAG
                    </span>
                </Link>
            </div>

            {/* Navigation */}
            <nav className="flex flex-col gap-1.5 p-6 pt-12">
                {navItems.map((item) => {
                    const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "group relative flex items-center gap-4 rounded-xl px-5 py-4 text-sm font-medium transition-refined",
                                isActive
                                    ? "bg-accent-subtle text-accent-hover shadow-refined-sm"
                                    : "text-muted hover:bg-secondary hover:text-fg"
                            )}
                        >
                            {/* Active indicator - thin left accent */}
                            {isActive && (
                                <div className="absolute left-0 top-1/2 -translate-y-1/2 h-8 w-1 bg-accent rounded-r-full" />
                            )}
                            <item.icon className={cn(
                                "h-5 w-5 transition-refined",
                                isActive ? "text-accent" : "text-muted group-hover:text-fg"
                            )} />
                            <span className="font-body">{item.label}</span>
                        </Link>
                    );
                })}
            </nav>

            {/* Footer space for potential user info or settings */}
            <div className="absolute bottom-0 left-0 right-0 p-6 border-t border-border/50">
                <div className="text-xs text-muted text-center font-body">
                    v1.0.0
                </div>
            </div>
        </aside>
    );
}
