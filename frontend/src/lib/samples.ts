/**
 * The Product shape the scan report and manufacturer pages show, plus the two
 * built-in sample reports ("True product" / "False product" on the scan page).
 * Real data comes from the backend through src/lib/api.ts.
 */

export type Scan = { time: string; place: string; flagged?: boolean };

export type Product = {
  code: string;
  name: string;
  batch: string;
  sku?: string | undefined;
  facility?: string | undefined;
  manufacturer: string;
  distributors: { name: string; address: string }[];
  txHash: string | null;
  block: number | null;
  onChain?: boolean | undefined;
  /** Public block-explorer page for the registration transaction (e.g. Etherscan). */
  explorerUrl?: string | null | undefined;
  scans: Scan[];
  anomalies: string[];
};

const SAMPLES: Record<string, Product> = {
  "AQ-1001": {
    code: "AQ-1001",
    name: "Herbal Green Tea 100 g",
    batch: "B-0427",
    manufacturer: "Sahyadri Foods (sample)",
    distributors: [{ name: "Godavari Traders", address: "College Road, Nashik" }],
    txHash: "0x8f3a1c97d2b44e0a6c1f5b7e9a3d2c4b8e6f0a1d",
    block: 1042,
    scans: [
      { time: "28 Sep, 16:05", place: "Nashik" },
      { time: "30 Sep, 11:20", place: "Nashik" },
    ],
    anomalies: [],
  },
  "AQ-2002": {
    code: "AQ-2002",
    name: "Vitamin C Tablets, 30 pack",
    batch: "B-0913",
    manufacturer: "Sahyadri Foods (sample)",
    distributors: [{ name: "Western Medico", address: "Andheri East, Mumbai" }],
    txHash: "0x2b7e44a09c1d3f5e8a6b0c2d4e6f8a1b3c5d7e9f",
    block: 1187,
    scans: [
      { time: "Today, 10:42", place: "Mumbai" },
      { time: "Today, 10:42", place: "London", flagged: true },
    ],
    anomalies: [
      "This code was scanned in Mumbai and London at the same time. The code may have been copied.",
    ],
  },
};

export const SAMPLE_REPORTS = { genuine: "AQ-1001", fake: "AQ-2002" } as const;

export function sampleProduct(code: string): Product | null {
  return SAMPLES[code] ?? null;
}
