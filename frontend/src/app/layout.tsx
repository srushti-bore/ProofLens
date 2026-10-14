import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ProofLens AI — From Documents to Verifiable Answers',
  description:
    'Evidence-first document intelligence platform enforcing strict citation provenance, 4-tier claim verification, and tenant isolation.',
  keywords: [
    'Document Intelligence',
    'Evidence-First RAG',
    'Provenance',
    'Gemini AI',
    'Citation Verification',
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
