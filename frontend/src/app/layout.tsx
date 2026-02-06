import type { Metadata } from "next";
import { Cormorant_Garamond, Inter, Geist_Mono } from "next/font/google";
import "./globals.css";

// Elegant serif for display headings
const cormorantGaramond = Cormorant_Garamond({
  weight: ['400', '500', '600', '700'],
  variable: "--font-display",
  subsets: ["latin"],
  display: 'swap',
});

// Refined grotesque sans-serif for body text
const inter = Inter({
  variable: "--font-body",
  subsets: ["latin"],
  display: 'swap',
});

// Keep mono font for code
const geistMono = Geist_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  display: 'swap',
});

export const metadata: Metadata = {
  title: "GraphRAG Agent - Intelligent Document Analysis",
  description: "A sophisticated GraphRAG-powered agent for intelligent document analysis and knowledge extraction.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${cormorantGaramond.variable} ${inter.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
