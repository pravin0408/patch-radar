import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Unified Hardware Patch & Advisory Radar",
  description: "Aggregated patch, firmware, and advisory data across Dell, Cisco, NetScaler, and HPE.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
