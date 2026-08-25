import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const html = readFileSync(resolve(root, 'leads_dashboard.html'), 'utf8');

writeFileSync(
  resolve(root, 'app/dashboard-html.ts'),
  `export const dashboardHtml = ${JSON.stringify(html)};\n`,
);
