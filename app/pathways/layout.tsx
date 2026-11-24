import type { Metadata } from 'next';

export const metadata: Metadata = {title: 'Learning pathways | SAIRE Academy',
  description: 'Explore AI Engineering and original Computing & IT foundations, with clear outcomes and authored-content labels.'};

export default function PathwaysLayout({children}: {children: React.ReactNode}) {
  return children;
}
