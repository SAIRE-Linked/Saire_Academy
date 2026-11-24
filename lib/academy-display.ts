export function count(value: number, singular: string, plural = singular + 's') {
  return `${value} ${value === 1 ? singular : plural}`;
}

export function timeframe(value: string) {
  const text = String(value ?? '').trim();
  if (!text) return 'To be confirmed';
  if (/^\d+(?:[.,]\d+)?(?:\s*[-–—]\s*\d+(?:[.,]\d+)?)?$/.test(text)) {
    return `${text} ${Number(text) === 1 ? 'month' : 'months'}`;
  }
  return text;
}

export function dashboardDestination(value: string | null) {
  if (!value) return '/dashboard/';
  try {
    const url = new URL(value, 'https://academy.invalid');
    if (!value.startsWith('/') || url.origin !== 'https://academy.invalid' ||
        !['/dashboard/', '/dashboard'].includes(url.pathname)) return '/dashboard/';
    return '/dashboard/' + url.search + url.hash;
  } catch { return '/dashboard/'; }
}
