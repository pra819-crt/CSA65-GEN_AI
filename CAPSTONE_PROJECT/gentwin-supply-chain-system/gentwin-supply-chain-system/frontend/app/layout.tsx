import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";

export const metadata: Metadata = {
  title: "GenTwin — Supply Chain Resilience System",
  description:
    "Generative AI & Digital Twin-Based Supply Chain Resilience & Disruption Management System",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <div className="min-h-screen">
          <AuthProvider>{children}</AuthProvider>
        </div>
      </body>
    </html>
  );
}
