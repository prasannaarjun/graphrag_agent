"use client";

import { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

interface AppShellProps {
    children: ReactNode;
    title?: string;
}

export function AppShell({ children, title = "Dashboard" }: AppShellProps) {
    return (
        <div className="flex h-screen bg-bg">
            {/* Sidebar */}
            <Sidebar />

            {/* Main content area */}
            <div className="flex flex-1 flex-col overflow-hidden">
                {/* Top bar */}
                <TopBar title={title} />

                {/* Page content with generous padding and fade-in animation */}
                <main className="flex-1 flex flex-col overflow-hidden px-8 py-6 lg:px-12 lg:py-8 animate-fade-in">
                    <div className="mx-auto max-w-7xl w-full flex-1 flex flex-col min-h-0 overflow-y-auto">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
}
