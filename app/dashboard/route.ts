import { dashboardHtml } from '../dashboard-html';

export const runtime = 'edge';

export function GET() {
  return new Response(dashboardHtml, {
    headers: {
      'content-type': 'text/html; charset=utf-8',
      'cache-control': 'public, max-age=60',
    },
  });
}
