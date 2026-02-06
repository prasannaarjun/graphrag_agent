"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Upload, FileText, Trash2, Search, Loader2, CloudUpload } from "lucide-react";
import { api } from "@/lib/api";

interface Document {
    id: string;
    filename: string;
    size: number;
    uploaded_at: string;
}

export default function KnowledgeBasePage() {
    const [documents, setDocuments] = useState<Document[]>([]);
    const [searchQuery, setSearchQuery] = useState("");
    const [isDragging, setIsDragging] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Load documents on mount
    useEffect(() => {
        loadDocuments();
    }, []);

    const loadDocuments = async () => {
        try {
            const data = await api.documents.list();
            setDocuments(data.documents);
        } catch (error) {
            console.error("Failed to load documents:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleUpload = async (files: FileList | File[]) => {
        setIsUploading(true);
        try {
            for (const file of Array.from(files)) {
                await api.documents.upload(file);
            }
            await loadDocuments(); // Refresh list
        } catch (error) {
            console.error("Upload failed:", error);
            alert(error instanceof Error ? error.message : "Upload failed");
        } finally {
            setIsUploading(false);
        }
    };

    const handleDelete = async (docId: string) => {
        if (!confirm("Are you sure you want to delete this document?")) return;
        try {
            await api.documents.delete(docId);
            setDocuments((prev) => prev.filter((d) => d.id !== docId));
        } catch (error) {
            console.error("Delete failed:", error);
            alert(error instanceof Error ? error.message : "Delete failed");
        }
    };

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleUpload(files);
        }
    }, []);

    const filteredDocs = documents.filter((doc) =>
        doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const formatSize = (bytes: number) => {
        if (bytes < 1024) return `${bytes} B`;
        if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
        return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    };

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric"
        });
    };

    return (
        <div className="space-y-10">
            {/* Header */}
            <div className="animate-fade-in">
                <h1 className="font-display text-4xl font-semibold text-fg tracking-tight mb-3">
                    Knowledge Base
                </h1>
                <p className="font-body text-lg text-muted">
                    Manage your documents and data sources for intelligent querying.
                </p>
            </div>

            {/* Elegant Upload Zone */}
            <Card
                className={`border-2 border-dashed transition-refined animate-slide-up ${
                    isDragging
                        ? "border-accent bg-accent-subtle/30 scale-[1.02]"
                        : "border-border/50"
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
            >
                <CardContent className="flex flex-col items-center justify-center py-16">
                    <div className="mb-6 h-20 w-20 rounded-2xl bg-gradient-to-br from-accent to-accent-hover flex items-center justify-center shadow-refined-lg transition-refined-slow hover:scale-110">
                        {isUploading ? (
                            <Loader2 className="h-10 w-10 animate-spin text-primary-foreground" />
                        ) : (
                            <CloudUpload className="h-10 w-10 text-primary-foreground" />
                        )}
                    </div>
                    <h3 className="font-display text-2xl font-semibold text-fg tracking-tight mb-2">
                        {isUploading ? "Uploading your files..." : "Upload Documents"}
                    </h3>
                    <p className="text-center font-body text-base text-muted mb-6">
                        {isUploading ? (
                            "Processing and indexing documents"
                        ) : (
                            <>
                                Drag and drop files here, or{" "}
                                <button
                                    className="text-accent hover:text-accent-hover transition-refined font-medium underline underline-offset-2"
                                    onClick={() => fileInputRef.current?.click()}
                                >
                                    browse files
                                </button>
                            </>
                        )}
                    </p>
                    <div className="flex gap-2 flex-wrap justify-center">
                        {["PDF", "TXT", "MD", "CSV", "HTML"].map((type) => (
                            <span
                                key={type}
                                className="px-3 py-1.5 text-xs font-medium font-body bg-accent-subtle text-accent rounded-lg"
                            >
                                {type}
                            </span>
                        ))}
                    </div>
                    <input
                        ref={fileInputRef}
                        type="file"
                        className="hidden"
                        multiple
                        accept=".pdf,.txt,.md,.csv,.html,.json"
                        onChange={(e) => e.target.files && handleUpload(e.target.files)}
                    />
                </CardContent>
            </Card>

            {/* Documents Table with refined styling */}
            <Card className="animate-slide-up animate-delay-1">
                <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="font-display text-2xl">
                        Documents <span className="text-muted font-body text-base">({documents.length})</span>
                    </CardTitle>
                    <div className="relative w-72">
                        <Search className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
                        <Input
                            placeholder="Search documents..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-11"
                        />
                    </div>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="flex items-center justify-center py-16">
                            <Loader2 className="h-8 w-8 animate-spin text-muted" />
                        </div>
                    ) : documents.length === 0 ? (
                        <div className="py-16 text-center">
                            <FileText className="h-12 w-12 mx-auto mb-4 text-muted" />
                            <p className="font-body text-lg text-muted mb-2">
                                No documents yet
                            </p>
                            <p className="font-body text-sm text-muted">
                                Upload your first document to get started
                            </p>
                        </div>
                    ) : (
                        <div className="rounded-lg border border-border/50 overflow-hidden">
                            <Table>
                                <TableHeader>
                                    <TableRow className="border-border/50 bg-accent-subtle/20">
                                        <TableHead className="font-body font-medium">Name</TableHead>
                                        <TableHead className="font-body font-medium">Size</TableHead>
                                        <TableHead className="font-body font-medium">Uploaded</TableHead>
                                        <TableHead className="w-12"></TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {filteredDocs.map((doc, index) => (
                                        <TableRow
                                            key={doc.id}
                                            className="border-border/50 transition-refined hover:bg-accent-subtle/20 animate-fade-in"
                                            style={{ animationDelay: `${index * 40}ms` }}
                                        >
                                            <TableCell className="font-body">
                                                <div className="flex items-center gap-3">
                                                    <div className="h-9 w-9 rounded-lg bg-accent-subtle flex items-center justify-center">
                                                        <FileText className="h-4 w-4 text-accent" />
                                                    </div>
                                                    <span className="font-medium text-fg">{doc.filename}</span>
                                                </div>
                                            </TableCell>
                                            <TableCell className="font-body text-muted">
                                                {formatSize(doc.size)}
                                            </TableCell>
                                            <TableCell className="font-body text-muted">
                                                {formatDate(doc.uploaded_at)}
                                            </TableCell>
                                            <TableCell>
                                                <Button
                                                    variant="ghost"
                                                    size="icon-sm"
                                                    className="hover:bg-destructive/10 hover:text-destructive transition-refined"
                                                    onClick={() => handleDelete(doc.id)}
                                                >
                                                    <Trash2 className="h-4 w-4" />
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
