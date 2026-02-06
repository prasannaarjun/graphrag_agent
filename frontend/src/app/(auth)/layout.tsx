import { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
    return (
        <div className="flex min-h-screen bg-bg">
            {/* Left side - Brand & Messaging (40%) */}
            <div className="hidden lg:flex lg:w-2/5 relative overflow-hidden bg-gradient-to-br from-accent via-accent-hover to-accent p-16 flex-col justify-between">
                {/* Subtle pattern overlay */}
                <div className="absolute inset-0 opacity-10">
                    <svg width="100%" height="100%">
                        <pattern id="graph-pattern" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
                            <circle cx="2" cy="2" r="1" fill="currentColor" />
                            <circle cx="20" cy="20" r="1" fill="currentColor" />
                            <line x1="2" y1="2" x2="20" y2="20" stroke="currentColor" strokeWidth="0.5" opacity="0.5" />
                        </pattern>
                        <rect width="100%" height="100%" fill="url(#graph-pattern)" />
                    </svg>
                </div>

                {/* Content */}
                <div className="relative z-10 animate-fade-in">
                    {/* Brand lockup */}
                    <div className="flex items-center gap-4 mb-16">
                        <div className="h-14 w-14 rounded-xl bg-white/10 backdrop-blur-sm flex items-center justify-center shadow-refined-lg">
                            <svg
                                className="h-8 w-8 text-primary-foreground"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            >
                                <circle cx="18" cy="5" r="3" />
                                <circle cx="6" cy="12" r="3" />
                                <circle cx="18" cy="19" r="3" />
                                <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
                                <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
                            </svg>
                        </div>
                        <h1 className="font-display text-4xl font-semibold text-primary-foreground tracking-tight">
                            GraphRAG
                        </h1>
                    </div>

                    {/* Value proposition */}
                    <div className="space-y-8 max-w-md">
                        <h2 className="font-display text-3xl font-medium text-primary-foreground leading-snug">
                            Intelligent document analysis powered by knowledge graphs
                        </h2>
                        <p className="font-body text-lg text-primary-foreground/80 leading-relaxed">
                            Transform your documents into actionable insights with sophisticated graph-based reasoning and multi-tenant architecture.
                        </p>
                    </div>
                </div>

                {/* Footer note */}
                <div className="relative z-10 text-primary-foreground/60 font-body text-sm">
                    © 2026 GraphRAG Agent. Built with precision.
                </div>
            </div>

            {/* Right side - Auth forms (60%) */}
            <div className="flex-1 flex items-center justify-center p-8 lg:p-16">
                <div className="w-full max-w-md animate-slide-up">
                    {children}
                </div>
            </div>
        </div>
    );
}
