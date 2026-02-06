"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { FileText, MessageSquare, Activity, Plus, Upload, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

interface Conversation {
    id: string;
    title: string | null;
    created_at: string;
    message_count: number;
}

export default function DashboardPage() {
    const router = useRouter();
    const [docCount, setDocCount] = useState<number | null>(null);
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isHealthy, setIsHealthy] = useState<boolean | null>(null);

    useEffect(() => {
        async function loadData() {
            try {
                // Load documents count - this requires auth
                const docs = await api.documents.list();
                setDocCount(docs.total);

                // Load conversations
                const convs = await api.chat.getConversations();
                setConversations(convs.conversations);

                setIsHealthy(true);
            } catch (error) {
                console.error("Failed to load dashboard data:", error);

                // Check if it's an auth error
                if (error instanceof Error && error.message.includes("authentication")) {
                    // Clear invalid token and redirect to login
                    localStorage.removeItem("token");
                    router.push("/login");
                    return;
                }

                setIsHealthy(false);
            } finally {
                setIsLoading(false);
            }
        }

        loadData();
    }, [router]);

    const formatTime = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const days = Math.floor(hours / 24);

        if (hours < 1) return "Just now";
        if (hours < 24) return `${hours} hour${hours > 1 ? "s" : ""} ago`;
        if (days === 1) return "Yesterday";
        return `${days} days ago`;
    };

    return (
        <div className="space-y-12">
            {/* Header with generous padding */}
            <div className="flex items-start justify-between pt-8 animate-fade-in">
                <div>
                    <h1 className="font-display text-5xl font-semibold text-fg tracking-tight mb-4">
                        Welcome back
                    </h1>
                    <p className="font-body text-lg text-muted">
                        Here's an overview of your knowledge base.
                    </p>
                </div>
                <div className="flex gap-3">
                    <Button variant="outline" size="lg" asChild>
                        <Link href="/kb">
                            <Upload className="mr-2 h-5 w-5" />
                            Upload Document
                        </Link>
                    </Button>
                    <Button size="lg" asChild>
                        <Link href="/chat">
                            <Plus className="mr-2 h-5 w-5" />
                            New Chat
                        </Link>
                    </Button>
                </div>
            </div>

            {/* Stats Grid with staggered animations */}
            <div className="grid gap-6 md:grid-cols-3">
                <Card className="animate-slide-up animate-delay-0 hover:scale-[1.02] transition-refined-slow">
                    <CardHeader className="flex flex-row items-center justify-between pb-4">
                        <CardTitle className="text-sm font-medium text-muted font-body">
                            Documents Indexed
                        </CardTitle>
                        <div className="h-10 w-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                            <FileText className="h-5 w-5 text-accent" />
                        </div>
                    </CardHeader>
                    <CardContent>
                        {isLoading ? (
                            <Loader2 className="h-8 w-8 animate-spin text-muted" />
                        ) : (
                            <>
                                <div className="font-display text-5xl font-semibold text-fg tracking-tight mb-2">
                                    {docCount ?? 0}
                                </div>
                                <p className="text-sm text-muted font-body">Total documents in library</p>
                            </>
                        )}
                    </CardContent>
                </Card>

                <Card className="animate-slide-up animate-delay-1 hover:scale-[1.02] transition-refined-slow">
                    <CardHeader className="flex flex-row items-center justify-between pb-4">
                        <CardTitle className="text-sm font-medium text-muted font-body">
                            Conversations
                        </CardTitle>
                        <div className="h-10 w-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                            <MessageSquare className="h-5 w-5 text-accent" />
                        </div>
                    </CardHeader>
                    <CardContent>
                        {isLoading ? (
                            <Loader2 className="h-8 w-8 animate-spin text-muted" />
                        ) : (
                            <>
                                <div className="font-display text-5xl font-semibold text-fg tracking-tight mb-2">
                                    {conversations.length}
                                </div>
                                <p className="text-sm text-muted font-body">Active conversations</p>
                            </>
                        )}
                    </CardContent>
                </Card>

                <Card className="animate-slide-up animate-delay-2 hover:scale-[1.02] transition-refined-slow">
                    <CardHeader className="flex flex-row items-center justify-between pb-4">
                        <CardTitle className="text-sm font-medium text-muted font-body">
                            System Status
                        </CardTitle>
                        <div className="h-10 w-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                            <Activity className="h-5 w-5 text-accent" />
                        </div>
                    </CardHeader>
                    <CardContent>
                        {isLoading ? (
                            <Loader2 className="h-8 w-8 animate-spin text-muted" />
                        ) : (
                            <>
                                <div className="flex items-center gap-3 mb-2">
                                    <Badge
                                        variant={isHealthy ? "success" : "destructive"}
                                        className="text-sm font-body"
                                    >
                                        {isHealthy ? "Healthy" : "Offline"}
                                    </Badge>
                                </div>
                                <p className="text-sm text-muted font-body">
                                    {isHealthy ? "All services operational" : "Backend unavailable"}
                                </p>
                            </>
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Recent Activity with refined styling */}
            <Card className="animate-slide-up animate-delay-3">
                <CardHeader>
                    <CardTitle className="font-display text-2xl">Recent Conversations</CardTitle>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="flex justify-center py-12">
                            <Loader2 className="h-8 w-8 animate-spin text-muted" />
                        </div>
                    ) : conversations.length === 0 ? (
                        <div className="py-16 text-center">
                            <MessageSquare className="h-12 w-12 mx-auto mb-4 text-muted" />
                            <p className="font-body text-lg text-muted mb-6">
                                No conversations yet.
                            </p>
                            <Button size="lg" asChild>
                                <Link href="/chat">
                                    <Plus className="mr-2 h-5 w-5" />
                                    Start your first chat
                                </Link>
                            </Button>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {conversations.slice(0, 5).map((conv, index) => (
                                <Link
                                    key={conv.id}
                                    href={`/chat?id=${conv.id}`}
                                    className={`flex items-center justify-between rounded-xl border border-border/50 p-5 transition-refined hover:border-accent hover:bg-accent-subtle/30 hover:shadow-refined-md animate-fade-in`}
                                    style={{ animationDelay: `${index * 60}ms` }}
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="h-10 w-10 rounded-lg bg-accent-subtle flex items-center justify-center">
                                            <MessageSquare className="h-5 w-5 text-accent" />
                                        </div>
                                        <div>
                                            <p className="font-body font-medium text-fg">
                                                {conv.title || `Conversation ${conv.id.slice(0, 8)}`}
                                            </p>
                                            <p className="text-sm text-muted font-body">
                                                {conv.message_count} {conv.message_count === 1 ? 'message' : 'messages'}
                                            </p>
                                        </div>
                                    </div>
                                    <span className="text-sm text-muted font-body">
                                        {formatTime(conv.created_at)}
                                    </span>
                                </Link>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
