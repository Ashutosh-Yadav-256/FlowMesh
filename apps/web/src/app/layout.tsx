import type { Metadata } from "next";
import { Urbanist } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import { Header } from "@/components/Header";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { OnboardingModal } from "@/components/OnboardingModal";
import { OnboardingChecklist } from "@/components/OnboardingChecklist";

const urbanist = Urbanist({
  subsets: ["latin"],
  variable: "--font-urbanist",
  display: "swap",
  weight: ["300", "400", "500", "600", "700", "800", "900"],
});

export const metadata: Metadata = {
  title: "FlowMesh — Enterprise Integration & Workflow Platform",
  description:
    "Client-owned, cloud-neutral enterprise integration and workflow platform with Edge Agent, Control Plane, Data Plane, and RediForge StateStore.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`light ${urbanist.variable}`} suppressHydrationWarning>
      <body className={`${urbanist.className} text-[#1B1B1B] min-h-screen antialiased font-sans selection:bg-terracotta-600/20 selection:text-carbon`}>
        <Sidebar />
        <div className="flex flex-col min-h-screen">
          <Header />
          <main className="lg:ml-64 ml-0 p-4 lg:p-8 flex-1">
            <ErrorBoundary>
              {children}
            </ErrorBoundary>
          </main>
        </div>
        <OnboardingModal />
        <OnboardingChecklist />
      </body>
    </html>
  );
}

