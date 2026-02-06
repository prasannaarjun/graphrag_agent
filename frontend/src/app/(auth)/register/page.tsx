"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { api } from "@/lib/api";

export default function RegisterPage() {
    const router = useRouter();
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError("");

        try {
            const data = await api.auth.register(email, password, name || undefined);
            localStorage.setItem("token", data.access_token);
            router.push("/dashboard");
        } catch (err) {
            setError(err instanceof Error ? err.message : "Registration failed");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="w-full animate-fade-in">
            {/* Elegant heading */}
            <div className="mb-12 text-center lg:text-left">
                <h1 className="font-display text-4xl md:text-5xl font-semibold text-fg tracking-tight mb-3">
                    Get started
                </h1>
                <p className="font-body text-muted text-base">
                    Create your account to begin exploring knowledge graphs
                </p>
            </div>

            <Card className="border-border/50 shadow-refined-lg">
                <CardContent className="pt-8">
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {error && (
                            <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-4 text-sm text-destructive font-body animate-slide-down">
                                {error}
                            </div>
                        )}
                        <div className="space-y-2.5 animate-fade-in animate-delay-1">
                            <label htmlFor="name" className="text-sm font-medium text-fg font-body">
                                Full name
                            </label>
                            <Input
                                id="name"
                                type="text"
                                placeholder="John Doe"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="h-12"
                            />
                            <p className="text-xs text-muted font-body">Optional: This helps personalize your experience</p>
                        </div>
                        <div className="space-y-2.5 animate-fade-in animate-delay-2">
                            <label htmlFor="email" className="text-sm font-medium text-fg font-body">
                                Email address
                            </label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="you@example.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="h-12"
                            />
                        </div>
                        <div className="space-y-2.5 animate-fade-in animate-delay-3">
                            <label htmlFor="password" className="text-sm font-medium text-fg font-body">
                                Password
                            </label>
                            <Input
                                id="password"
                                type="password"
                                placeholder="Create a strong password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                                minLength={8}
                                className="h-12"
                            />
                            <p className="text-xs text-muted font-body">Minimum 8 characters</p>
                        </div>
                        <Button
                            type="submit"
                            size="lg"
                            className="w-full animate-fade-in animate-delay-4"
                            disabled={isLoading}
                        >
                            {isLoading ? "Creating account..." : "Create account"}
                        </Button>
                        <p className="text-xs text-center text-muted font-body animate-fade-in animate-delay-4">
                            By creating an account, you agree to our Terms of Service and Privacy Policy.
                        </p>
                    </form>
                </CardContent>
                <CardFooter className="justify-center border-t border-border/50 mt-8 pt-6">
                    <p className="text-sm text-muted font-body">
                        Already have an account?{" "}
                        <Link href="/login" className="text-accent hover:text-accent-hover transition-refined font-medium">
                            Sign in
                        </Link>
                    </p>
                </CardFooter>
            </Card>
        </div>
    );
}
