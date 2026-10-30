import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "SAIRE-Linked Digital Learning | AI Engineering Mastery",
  description: "Build smarter. Learn deeper. A project-based path from programming foundations to advanced AI and agent engineering by SAIRE-Linked.",
  keywords: ["SAIRE-Linked", "Digital Learning Platform", "AI Engineer", "AI Agents", "Programming", "Software Engineering"],
  openGraph: {
    title: "SAIRE-Linked Digital Learning Platform",
    description: "From your first Python program to production-ready AI agents.",
    type: "website"
  }
};
export default function RootLayout({ children }: Readonly<{children: React.ReactNode}>) {
  return <html lang="en"><body>{children}</body></html>;
}
