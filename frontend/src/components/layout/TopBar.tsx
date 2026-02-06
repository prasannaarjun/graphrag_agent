"use client";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Menu, LogOut, User } from "lucide-react";

interface TopBarProps {
    title: string;
}

export function TopBar({ title }: TopBarProps) {
    return (
        <header className="flex h-20 items-center justify-between border-b border-border/50 bg-card/50 backdrop-blur-sm px-8">
            {/* Mobile menu button */}
            <Button variant="ghost" size="icon" className="lg:hidden">
                <Menu className="h-5 w-5" />
            </Button>

            {/* Page title with refined typography */}
            <h1 className="font-display text-3xl font-semibold text-fg tracking-tight">
                {title}
            </h1>

            {/* User menu with refined interactions */}
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button
                        variant="ghost"
                        className="relative h-10 w-10 rounded-full transition-refined hover:ring-2 hover:ring-accent/20 hover:ring-offset-2"
                    >
                        <Avatar className="h-10 w-10">
                            <AvatarImage src="" alt="User" />
                            <AvatarFallback className="bg-gradient-to-br from-accent to-accent-hover text-primary-foreground font-body font-medium">
                                U
                            </AvatarFallback>
                        </Avatar>
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                    align="end"
                    className="w-56 shadow-refined-lg animate-slide-down"
                >
                    <div className="px-3 py-3 border-b border-border/50">
                        <p className="text-sm font-medium font-body text-fg">User Account</p>
                        <p className="text-xs text-muted font-body">user@example.com</p>
                    </div>
                    <DropdownMenuItem className="py-3 cursor-pointer transition-refined">
                        <User className="mr-3 h-4 w-4" />
                        <span className="font-body">Profile</span>
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem className="py-3 text-destructive cursor-pointer transition-refined focus:text-destructive">
                        <LogOut className="mr-3 h-4 w-4" />
                        <span className="font-body">Log out</span>
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>
        </header>
    );
}
