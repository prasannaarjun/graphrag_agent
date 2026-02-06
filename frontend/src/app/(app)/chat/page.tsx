"use client";

import { useState, useRef, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Send, Loader2, Sparkles } from "lucide-react";
import { api } from "@/lib/api";

interface Message {
    id: string;
    role: "user" | "assistant";
    content: string;
}

export default function ChatPage() {
    const searchParams = useSearchParams();
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isStreaming, setIsStreaming] = useState(false);
    const [isLoadingConversation, setIsLoadingConversation] = useState(false);
    const [conversationId, setConversationId] = useState<string | undefined>();
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Load existing conversation if ?id= is present
    useEffect(() => {
        const id = searchParams.get("id");
        if (!id) return;

        setIsLoadingConversation(true);
        api.chat
            .getConversation(id)
            .then((conv) => {
                setConversationId(conv.id);
                setMessages(
                    conv.messages.map((msg) => ({
                        id: msg.id,
                        role: msg.role as "user" | "assistant",
                        content: msg.content,
                    }))
                );
            })
            .catch((err) => {
                console.error("Failed to load conversation:", err);
            })
            .finally(() => {
                setIsLoadingConversation(false);
            });
    }, [searchParams]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isStreaming) return;

        const userMessage: Message = {
            id: Date.now().toString(),
            role: "user",
            content: input.trim(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setIsStreaming(true);

        // Create placeholder for assistant response
        const assistantId = (Date.now() + 1).toString();
        setMessages((prev) => [
            ...prev,
            { id: assistantId, role: "assistant", content: "" },
        ]);

        try {
            const response = await api.chat.streamMessage(
                userMessage.content,
                conversationId
            );

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            if (reader) {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    const lines = chunk.split("\n");

                    for (const line of lines) {
                        if (line.startsWith("data: ")) {
                            const data = line.slice(6);
                            if (data === "[DONE]") continue;

                            try {
                                const parsed = JSON.parse(data);

                                // Capture conversation ID from first response
                                if (parsed.conversation_id && !conversationId) {
                                    setConversationId(parsed.conversation_id);
                                }

                                if (parsed.content) {
                                    setMessages((prev) =>
                                        prev.map((msg) =>
                                            msg.id === assistantId
                                                ? { ...msg, content: msg.content + parsed.content }
                                                : msg
                                        )
                                    );
                                }
                            } catch {
                                // Non-JSON chunk, append as text
                                if (data.trim()) {
                                    setMessages((prev) =>
                                        prev.map((msg) =>
                                            msg.id === assistantId
                                                ? { ...msg, content: msg.content + data }
                                                : msg
                                        )
                                    );
                                }
                            }
                        }
                    }
                }
            }
        } catch (error) {
            console.error("Stream error:", error);
            setMessages((prev) =>
                prev.map((msg) =>
                    msg.id === assistantId
                        ? { ...msg, content: "Error: Failed to get response. Please try again." }
                        : msg
                )
            );
        } finally {
            setIsStreaming(false);
        }
    };

    const suggestedPrompts = [
        "Summarize the key insights from my documents",
        "What are the main themes in my knowledge base?",
        "Find connections between different documents",
    ];

    return (
        <div className="flex flex-1 min-h-0 flex-col">
            {/* Messages area */}
            <div className="flex-1 overflow-y-auto pb-6">
                {isLoadingConversation ? (
                    <div className="flex h-full items-center justify-center animate-fade-in">
                        <div className="text-center">
                            <Loader2 className="h-8 w-8 animate-spin text-muted mx-auto mb-4" />
                            <p className="font-body text-muted">Loading conversation...</p>
                        </div>
                    </div>
                ) : messages.length === 0 ? (
                    <div className="flex h-full items-center justify-center animate-fade-in">
                        <div className="text-center max-w-2xl px-4">
                            <div className="mb-8 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-accent to-accent-hover shadow-refined-lg">
                                <Sparkles className="h-8 w-8 text-primary-foreground" />
                            </div>
                            <h2 className="font-display text-4xl font-semibold text-fg tracking-tight mb-4">
                                Start a conversation
                            </h2>
                            <p className="font-body text-lg text-muted mb-12">
                                Ask questions about your knowledge base and get intelligent answers powered by graph reasoning.
                            </p>

                            {/* Suggested prompts */}
                            <div className="space-y-3">
                                <p className="text-sm font-medium text-muted font-body mb-4">Try asking:</p>
                                {suggestedPrompts.map((prompt, index) => (
                                    <button
                                        key={index}
                                        onClick={() => setInput(prompt)}
                                        className="w-full text-left px-6 py-4 rounded-xl border border-border/50 bg-card hover:border-accent hover:bg-accent-subtle/30 transition-refined shadow-refined-sm hover:shadow-refined-md animate-fade-in"
                                        style={{ animationDelay: `${index * 80}ms` }}
                                    >
                                        <p className="font-body text-sm text-fg">{prompt}</p>
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-6 px-4">
                        {messages.map((message, index) => (
                            <div
                                key={message.id}
                                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"} animate-fade-in`}
                                style={{ animationDelay: `${index * 40}ms` }}
                            >
                                <div
                                    className={`max-w-[85%] rounded-2xl px-6 py-4 ${
                                        message.role === "user"
                                            ? "bg-accent text-primary-foreground shadow-refined-md"
                                            : "border border-border/50 bg-card shadow-refined-sm"
                                    }`}
                                >
                                    {message.role === "assistant" && (
                                        <div className="flex items-center gap-2 mb-3">
                                            <div className="h-6 w-6 rounded-lg bg-accent-subtle flex items-center justify-center">
                                                <Sparkles className="h-3.5 w-3.5 text-accent" />
                                            </div>
                                            <span className="text-xs font-medium text-accent font-body">AI Assistant</span>
                                        </div>
                                    )}
                                    <p className="whitespace-pre-wrap text-base leading-relaxed font-body">
                                        {message.content || (
                                            <span className="flex items-center gap-2 text-muted animate-breathing">
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                                Thinking...
                                            </span>
                                        )}
                                    </p>
                                </div>
                            </div>
                        ))}
                        <div ref={messagesEndRef} />
                    </div>
                )}
            </div>

            {/* Input area with refined styling */}
            <form onSubmit={handleSubmit} className="flex gap-3 pt-6 border-t border-border/50">
                <Textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask a question about your knowledge base..."
                    className="min-h-[64px] resize-none text-base"
                    onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault();
                            handleSubmit(e);
                        }
                    }}
                />
                <Button
                    type="submit"
                    size="lg"
                    className="px-6"
                    disabled={isStreaming || !input.trim()}
                >
                    {isStreaming ? (
                        <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                        <>
                            <Send className="h-5 w-5 mr-2" />
                            Send
                        </>
                    )}
                </Button>
            </form>
        </div>
    );
}
