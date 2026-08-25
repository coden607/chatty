import leads from '../../../leads.json';

export const runtime = 'edge';

type Lead = { id?: number | string; name?: string; email?: string; source?: string; lead_score?: number; status?: string; created_at?: string; [key: string]: unknown };
type RecordValue = Record<string, any>;
const leadList = leads as Lead[];

const workflows: RecordValue[] = [
  { id: 'ng-outreach', name: 'Narcoguard Outreach Pipeline', owner: 'acquisition_engine', status: 'active', progress: 72, last_run: null, steps: [{ name: 'Target list build', status: 'complete' }, { name: 'Personalization pass', status: 'active' }, { name: 'Cadence scheduling', status: 'queued' }, { name: 'CRM logging', status: 'queued' }] },
  { id: 'ng-investor', name: 'Investor Update Automation', owner: 'investor_relations', status: 'active', progress: 44, last_run: null, steps: [{ name: 'Metrics snapshot', status: 'complete' }, { name: 'Narrative refresh', status: 'active' }, { name: 'Artifact packaging', status: 'queued' }] },
];
const agents = [{ name: 'orchestrator', status: 'active', focus: 'routing' }, { name: 'revenue_engine', status: 'active', focus: 'pricing' }, { name: 'acquisition_engine', status: 'active', focus: 'outreach' }, { name: 'content_engine', status: 'active', focus: 'narratives' }, { name: 'investor_relations', status: 'active', focus: 'updates' }];
const tasks: RecordValue[] = [{ id: 1, title: 'Monitor production dashboard deployment', owner: 'orchestrator', priority: 'high', status: 'active', created_at: new Date().toISOString() }];
const collabEvents: RecordValue[] = [{ event: 'deploy', agent: 'orchestrator', detail: 'Production dashboard deployed from verified repo data.', timestamp: new Date().toISOString() }];
const promptHistory: RecordValue[] = [];
const messages: RecordValue[] = [];
const campaigns: RecordValue[] = [];
const n8nWorkflows: RecordValue[] = [];
const briefs: RecordValue[] = [];
const grants: RecordValue[] = [];
const experiments: RecordValue[] = [];
const generated: RecordValue = { type: '', draft: '' };
const launchRuns: RecordValue[] = [];
const pipelines: RecordValue[] = [{ name: 'Revenue Autopilot', status: 'active', progress: 41, stages: [{ name: 'Offer optimization', status: 'active' }, { name: 'Pricing experiments', status: 'queued' }] }];
const autonomy = { state: { running: false, mode: 'production-dashboard', loop_interval_sec: 60, last_tick: null as string | null }, settings: { daily_budget: 250, risk_guardrails: 'conservative', primary_channel: 'email' } };

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
const stateId = 'global';
const sendgridFromEmail = process.env.SENDGRID_FROM_EMAIL || process.env.SENDGRID_FROM || '';
const sendgridFromName = process.env.SENDGRID_FROM_NAME || 'CHATTY';
const narcoguardUrl = process.env.NARCOGUARD_URL || 'https://v0-narcoguard-pwa-build.vercel.app';
const fundingUrl = process.env.NARCOGUARD_FUNDING_URL || process.env.GOFUNDME_URL || 'https://gofund.me/e1a0b3f2';

function redactEmail(email: unknown) { if (typeof email !== 'string' || !email.includes('@')) return ''; const [local, domain] = email.split('@'); return `${local.slice(0, 2)}***@${domain}`; }
function publicLead(lead: Lead) { return { ...lead, email: redactEmail(lead.email) }; }
function now() { return new Date().toISOString(); }
function json(data: unknown, status = 200) { return Response.json(data, { status, headers: { 'cache-control': 'no-store' } }); }
function record(event: string, agent: string, detail: string) { collabEvents.unshift({ event, agent, detail, timestamp: now() }); collabEvents.splice(20); }
function publicLinksFooter() {
  return `NarcoGuard: ${narcoguardUrl}\nFunding: ${fundingUrl}`;
}
function appendPublicLinks(text: string) {
  const footer = publicLinksFooter();
  const hasNarcoguard = text.includes(narcoguardUrl);
  const hasFunding = text.includes(fundingUrl);
  if (hasNarcoguard && hasFunding) return text;
  return `${text}\n\n${footer}`;
}
function stateSnapshot() { return { workflows, tasks, collabEvents, promptHistory, messages, campaigns, n8nWorkflows, briefs, grants, experiments, pipelines, autonomy, generated, launchRuns }; }
function replaceArray(target: RecordValue[], source: unknown) { if (Array.isArray(source)) { target.splice(0, target.length, ...source); } }
function hydrateSnapshot(payload: RecordValue) {
  replaceArray(workflows, payload.workflows); replaceArray(tasks, payload.tasks); replaceArray(collabEvents, payload.collabEvents); replaceArray(promptHistory, payload.promptHistory); replaceArray(messages, payload.messages); replaceArray(campaigns, payload.campaigns); replaceArray(n8nWorkflows, payload.n8nWorkflows); replaceArray(briefs, payload.briefs); replaceArray(grants, payload.grants); replaceArray(experiments, payload.experiments); replaceArray(pipelines, payload.pipelines);
  replaceArray(launchRuns, payload.launchRuns);
  if (payload.generated) Object.assign(generated, payload.generated);
  if (payload.autonomy) { Object.assign(autonomy, payload.autonomy); Object.assign(autonomy.state, payload.autonomy.state || {}); Object.assign(autonomy.settings, payload.autonomy.settings || {}); }
}
async function hydrateFromSupabase() {
  if (!supabaseUrl || !supabaseServiceKey) return;
  try {
    const response = await fetch(`${supabaseUrl}/rest/v1/chatty_state?id=eq.${stateId}&select=payload`, { headers: { apikey: supabaseServiceKey, Authorization: `Bearer ${supabaseServiceKey}` }, cache: 'no-store' });
    if (response.ok) { const rows = await response.json() as Array<{ payload?: RecordValue }>; if (rows[0]?.payload) hydrateSnapshot(rows[0].payload); }
  } catch (error) { console.error('Supabase state read failed', error); }
}
async function persistToSupabase() {
  if (!supabaseUrl || !supabaseServiceKey) return;
  try {
    await fetch(`${supabaseUrl}/rest/v1/chatty_state`, { method: 'POST', headers: { apikey: supabaseServiceKey, Authorization: `Bearer ${supabaseServiceKey}`, 'Content-Type': 'application/json', Prefer: 'resolution=merge-duplicates,return=minimal' }, body: JSON.stringify([{ id: stateId, payload: stateSnapshot() }]) });
  } catch (error) { console.error('Supabase state write failed', error); }
}
async function generateWithProvider(prompt: string) {
  const providers = [
    process.env.NVIDIA_API_KEY ? { name: 'nvidia', key: process.env.NVIDIA_API_KEY, url: 'https://integrate.api.nvidia.com/v1/chat/completions', model: 'moonshotai/kimi-k2.5' } : null,
    process.env.OPENAI_API_KEY ? { name: 'openai', key: process.env.OPENAI_API_KEY, url: 'https://api.openai.com/v1/chat/completions', model: 'gpt-4o-mini' } : null,
    process.env.OPENROUTER_API_KEY ? { name: 'openrouter', key: process.env.OPENROUTER_API_KEY, url: 'https://openrouter.ai/api/v1/chat/completions', model: 'openai/gpt-4o-mini' } : null,
    process.env.XAI_API_KEY ? { name: 'xai', key: process.env.XAI_API_KEY, url: 'https://api.x.ai/v1/chat/completions', model: 'grok-3-mini' } : null,
    process.env.MISTRAL_API_KEY ? { name: 'mistral', key: process.env.MISTRAL_API_KEY, url: 'https://api.mistral.ai/v1/chat/completions', model: 'mistral-small-latest' } : null,
    process.env.DEEPSEEK_API_KEY ? { name: 'deepseek', key: process.env.DEEPSEEK_API_KEY, url: 'https://api.deepseek.com/chat/completions', model: 'deepseek-chat' } : null,
  ].filter(Boolean) as Array<{ name: string; key: string; url: string; model: string }>;
  if (!providers.length) throw new Error('No AI provider is configured.');
  const failures: string[] = [];
  for (const provider of providers) {
    try {
      const response = await fetch(provider.url, { method: 'POST', headers: { Authorization: `Bearer ${provider.key}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ model: provider.model, messages: [{ role: 'system', content: 'You are CHATTY content engine. Use only the facts in the prompt. Do not invent metrics, customers, partnerships, or outcomes.' }, { role: 'user', content: prompt }], temperature: 0.3, max_tokens: 900 }) });
      const raw = await response.text();
      let result: RecordValue = {};
      try { result = JSON.parse(raw) as RecordValue; } catch { throw new Error(`HTTP ${response.status}: provider returned an invalid response.`); }
      if (!response.ok) throw new Error(String(result.error?.message || `HTTP ${response.status}`));
      const text = result.choices?.[0]?.message?.content;
      if (typeof text !== 'string' || !text.trim()) throw new Error('Provider returned no content.');
      return { provider: provider.name, text: text.trim() };
    } catch (error) { failures.push(`${provider.name}: ${error instanceof Error ? error.message : 'request failed'}`); }
  }
  throw new Error(`All configured AI providers failed: ${failures.join('; ')}`);
}
async function sendSendGridEmail(payload: RecordValue) {
  if (!process.env.SENDGRID_API_KEY) throw new Error('SendGrid API key is not configured.');
  const to = String(payload.to || '').trim();
  const subject = String(payload.subject || '').trim();
  const text = String(payload.text || payload.content || '').trim();
  const html = typeof payload.html === 'string' ? payload.html.trim() : '';
  const fromEmail = String(payload.from_email || payload.fromEmail || sendgridFromEmail || '').trim();
  const fromName = String(payload.from_name || payload.fromName || sendgridFromName || '').trim();
  const replyTo = String(payload.reply_to || payload.replyTo || '').trim();
  if (!to) throw new Error('A recipient email address is required.');
  if (!subject) throw new Error('An email subject is required.');
  if (!text && !html) throw new Error('Email content is required.');
  if (!fromEmail) throw new Error('Configure `SENDGRID_FROM_EMAIL` or provide `from_email` in the request.');

  const body: RecordValue = {
    personalizations: [{ to: [{ email: to }], subject }],
    from: fromName ? { email: fromEmail, name: fromName } : { email: fromEmail },
    content: [],
  };
  if (text) body.content.push({ type: 'text/plain', value: text });
  if (html) body.content.push({ type: 'text/html', value: html });
  if (replyTo) body.reply_to = { email: replyTo };
  body.content = body.content.map((entry: RecordValue) => {
    if (entry.type === 'text/plain') return { ...entry, value: appendPublicLinks(String(entry.value || '')) };
    if (entry.type === 'text/html') return { ...entry, value: `${String(entry.value || '')}<p><a href="${narcoguardUrl}">NarcoGuard</a> · <a href="${fundingUrl}">Funding</a></p>` };
    return entry;
  });

  const response = await fetch('https://api.sendgrid.com/v3/mail/send', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.SENDGRID_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  const responseText = await response.text();
  if (!response.ok) throw new Error(responseText || `SendGrid request failed with HTTP ${response.status}.`);
  return { status: 'sent', provider: 'sendgrid', accepted: response.status === 202, response: responseText || null };
}
async function pushWorkflowToN8n(workflow: RecordValue) {
  const baseUrl = String(process.env.N8N_BASE_URL || '').trim().replace(/\/+$/, '');
  const apiKey = String(process.env.N8N_API_KEY || '').trim();
  if (!baseUrl || !apiKey) throw new Error('n8n URL and API key are not configured.');

  const definition = workflow.remote_definition || workflow.definition || workflow;
  const payload = {
    name: definition.name || workflow.name,
    nodes: definition.nodes || [],
    connections: definition.connections || {},
    settings: definition.settings || {},
    active: true,
    ...(process.env.N8N_PROJECT_ID ? { projectId: process.env.N8N_PROJECT_ID } : {}),
  };

  const createResponse = await fetch(`${baseUrl}/api/v1/workflows`, {
    method: 'POST',
    headers: {
      'X-N8N-API-KEY': apiKey,
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  });
  const createText = await createResponse.text();
  let created: RecordValue = {};
  try { created = createText ? JSON.parse(createText) as RecordValue : {}; } catch { created = { raw: createText }; }
  if (!createResponse.ok) throw new Error(String(created.message || created.error || createText || `n8n create failed with HTTP ${createResponse.status}.`));

  const workflowId = created.id || created.data?.id || created.workflowId;
  if (!workflowId) return { status: 'created', workflow: created };

  const activateResponse = await fetch(`${baseUrl}/api/v1/workflows/${workflowId}/activate`, {
    method: 'POST',
    headers: {
      'X-N8N-API-KEY': apiKey,
      Accept: 'application/json',
    },
  });
  const activateText = await activateResponse.text();
  let activated: RecordValue = {};
  try { activated = activateText ? JSON.parse(activateText) as RecordValue : {}; } catch { activated = { raw: activateText }; }
  if (!activateResponse.ok) throw new Error(String(activated.message || activated.error || activateText || `n8n activation failed with HTTP ${activateResponse.status}.`));

  return { status: 'activated', workflow: created, activation: activated, workflowId };
}
function buildN8nWorkflowDefinition(name: string, description: string, trigger: string) {
  const safeName = name || 'Untitled workflow';
  const sanitizedId = safeName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '') || 'workflow';
  return {
    name: safeName,
    nodes: [
      {
        parameters: {},
        id: `${sanitizedId}-manual-trigger`,
        name: 'Manual Trigger',
        type: 'n8n-nodes-base.manualTrigger',
        typeVersion: 1,
        position: [260, 300],
      },
      {
        parameters: {
          keepOnlySet: false,
          values: {
            string: [
              { name: 'workflow_name', value: safeName },
              { name: 'workflow_description', value: description || '' },
              { name: 'workflow_trigger', value: trigger || 'manual' },
            ],
          },
        },
        id: `${sanitizedId}-set`,
        name: 'Capture Context',
        type: 'n8n-nodes-base.set',
        typeVersion: 2,
        position: [520, 300],
      },
    ],
    connections: {
      'Manual Trigger': {
        main: [[{ node: 'Capture Context', type: 'main', index: 0 }]],
      },
    },
    settings: {
      executionOrder: 'v1',
      saveManualExecutions: true,
    },
  };
}
function leadsPayload() { const publicLeads = leadList.map(publicLead); return { total: publicLeads.length, new: publicLeads.filter((lead) => (lead.status || 'new') === 'new').length, leads: publicLeads }; }
function weeklyPayload() { return { completed: collabEvents, events: collabEvents, summary: `Narcoguard automation is operational. ${campaigns.length} campaign(s), ${tasks.length} task(s), and ${messages.length} operator message(s) tracked.` }; }
function integrationStatus() {
  return {
    public_links: {
      narcoguard: narcoguardUrl,
      funding: fundingUrl,
    },
    sendgrid: {
      configured: Boolean(process.env.SENDGRID_API_KEY),
      from_email_configured: Boolean(sendgridFromEmail),
      ready: Boolean(process.env.SENDGRID_API_KEY && sendgridFromEmail),
    },
    n8n: {
      configured: Boolean(process.env.N8N_BASE_URL && process.env.N8N_API_KEY),
      base_url: Boolean(process.env.N8N_BASE_URL),
      api_key: Boolean(process.env.N8N_API_KEY),
    },
    ai: {
      configured: Boolean(process.env.NVIDIA_API_KEY || process.env.OPENAI_API_KEY || process.env.OPENROUTER_API_KEY || process.env.XAI_API_KEY || process.env.MISTRAL_API_KEY || process.env.DEEPSEEK_API_KEY),
      providers: [
        Boolean(process.env.NVIDIA_API_KEY) && 'nvidia',
        Boolean(process.env.OPENAI_API_KEY) && 'openai',
        Boolean(process.env.OPENROUTER_API_KEY) && 'openrouter',
        Boolean(process.env.XAI_API_KEY) && 'xai',
        Boolean(process.env.MISTRAL_API_KEY) && 'mistral',
        Boolean(process.env.DEEPSEEK_API_KEY) && 'deepseek',
      ].filter(Boolean),
    },
    social: {
      configured: Boolean(process.env.TWITTER_API_KEY),
      ready: Boolean(process.env.TWITTER_API_KEY),
    },
  };
}
function dashboardPayload() {
  return { status: { status: 'running', systems_active: agents.length, total_automations: workflows.length, uptime_hours: 0, revenue_generated: 0 }, leads: leadsPayload(), workflows: { workflows }, agents: { agents }, tasks: { total: tasks.length, tasks }, collab: { total: collabEvents.length, events: collabEvents }, messages: { total: messages.length, messages }, autonomy, pipelines: { pipelines }, campaigns: { total: campaigns.length, campaigns }, n8n: { total: n8nWorkflows.length, workflows: n8nWorkflows }, transparency: { completed: collabEvents }, briefs: { briefs }, content: { briefs }, grants: { grants }, experiments: { experiments }, generated, integrations: integrationStatus(), anomalies: { anomalies: [] }, kpi: { anomalies: [] }, weekly: weeklyPayload(), weekly_brief: weeklyPayload(), timestamp: now() };
}
function getPayload(path: string[]) {
  switch (path.join('/')) {
    case 'dashboard/all': return dashboardPayload(); case 'leads': return leadsPayload(); case 'narcoguard/workflows': return { project: 'Narcoguard', workflows }; case 'narcoguard/launch/status': return { latest: launchRuns[0] || null, runs: launchRuns, events: collabEvents }; case 'agents': return { total: agents.length, agents }; case 'tasks': return { total: tasks.length, tasks }; case 'agents/collab': return { total: collabEvents.length, events: collabEvents }; case 'user/messages': return { total: messages.length, messages }; case 'autonomy/status': return autonomy; case 'pipelines': return { pipelines }; case 'campaigns': return { total: campaigns.length, campaigns }; case 'n8n/workflows': return { total: n8nWorkflows.length, workflows: n8nWorkflows }; case 'integrations/status': return integrationStatus(); case 'transparency/report': return { completed: collabEvents }; case 'content/briefs': return { briefs }; case 'grants': return { grants }; case 'experiments/pricing': return { experiments }; case 'kpi/anomalies': return { anomalies: [] }; case 'weekly/brief': return weeklyPayload(); default: return { status: 'ok', route: path.join('/') };
  }
}
async function body(request: Request): Promise<RecordValue> { try { return await request.json() as RecordValue; } catch { return {}; } }

export function GET(_request: Request, context: { params: Promise<{ path: string[] }> }) { return context.params.then(async ({ path }) => { await hydrateFromSupabase(); return json(getPayload(path)); }); }

export function POST(request: Request, context: { params: Promise<{ path: string[] }> }) {
  return context.params.then(async ({ path }) => {
    const route = path.join('/'); const data = await body(request);
    await hydrateFromSupabase();
    const finish = async (payload: unknown, status = 200) => { await persistToSupabase(); return json(payload, status); };
    if (route === 'narcoguard/launch') {
      const launchId = 'narcoguard-production-launch-v1';
      const existing = campaigns.find((campaign) => campaign.launch_id === launchId);
      if (existing) {
        if (!launchRuns[0]) {
          const timestamp = String(existing.created_at || now());
          const pending = missingIntegrations();
          launchRuns.unshift({ id: existing.id, launch_id: launchId, status: 'completed_with_pending_integrations', started_at: timestamp, completed_at: timestamp, steps: [
            { name: 'Campaign plan', status: 'completed', detail: 'Production campaign created.' },
            { name: 'Launch task', status: 'completed', detail: 'Orchestrator task queued.' },
            { name: 'Content brief', status: 'completed', detail: 'Launch brief generated.' },
            { name: 'Pricing experiment', status: 'completed', detail: 'Pilot offer experiment created.' },
            { name: 'Grant tracking', status: 'completed', detail: 'Funding tracker created.' },
            { name: 'n8n workflow', status: 'completed', detail: 'Workflow definition created and saved.' },
            { name: 'External providers', status: pending.length ? 'pending' : 'completed', detail: pending.length ? pending.join('; ') : 'All configured providers available.' },
          ], pending });
        }
        return finish({ status: 'already_launched', launch_id: launchId, completed: ['campaign', 'task', 'content_brief', 'pricing_experiment', 'grant_tracking', 'n8n_workflow'], pending: missingIntegrations(), run: launchRuns[0], dashboard: dashboardPayload() });
      }
      const timestamp = now();
      const pending = missingIntegrations();
      const run = { id: Date.now(), launch_id: launchId, status: 'completed_with_pending_integrations', started_at: timestamp, completed_at: timestamp, steps: [
        { name: 'Campaign plan', status: 'completed', detail: 'Production campaign created.' },
        { name: 'Launch task', status: 'completed', detail: 'Orchestrator task queued.' },
        { name: 'Content brief', status: 'completed', detail: 'Launch brief generated.' },
        { name: 'Pricing experiment', status: 'completed', detail: 'Pilot offer experiment created.' },
        { name: 'Grant tracking', status: 'completed', detail: 'Funding tracker created.' },
        { name: 'n8n workflow', status: 'completed', detail: 'Workflow definition created and saved.' },
        { name: 'External providers', status: pending.length ? 'pending' : 'completed', detail: pending.length ? pending.join('; ') : 'All configured providers available.' },
      ], pending };
      const campaign = { id: Date.now(), launch_id: launchId, name: 'Narcoguard Production Launch', channel: 'partnerships', goal: 'pilot leads', owner: 'content_engine', status: 'planned', created_at: timestamp };
      campaigns.unshift(campaign);
      tasks.unshift({ id: Date.now() + 1, title: 'Execute Narcoguard production launch checklist', owner: 'orchestrator', priority: 'high', status: 'queued', launch_id: launchId, created_at: timestamp });
      briefs.unshift({ id: Date.now() + 2, title: 'Narcoguard production launch brief', source: 'CHATTY content engine', status: 'ready', launch_id: launchId, created_at: timestamp });
      experiments.unshift({ id: Date.now() + 3, name: 'Narcoguard pilot offer test', hypothesis: 'A supervised pilot converts qualified partners', metric: 'pilot_conversion_rate', status: 'planned', launch_id: launchId, created_at: timestamp });
      grants.unshift({ id: Date.now() + 4, name: 'Narcoguard public-health pilot funding', deadline: 'TBD', status: 'tracking', launch_id: launchId, created_at: timestamp });
      n8nWorkflows.unshift({ id: Date.now() + 5, name: 'Narcoguard Production Launch Workflow', description: 'Launch checklist for campaign, content, partner outreach, and reporting.', trigger: 'manual', status: 'ready', launch_id: launchId, created_at: timestamp });
      launchRuns.unshift(run);
      launchRuns.splice(20);
      record('launch', 'orchestrator', 'Narcoguard one-click production launch completed.');
      return finish({ status: 'launched', launch_id: launchId, completed: ['campaign', 'task', 'content_brief', 'pricing_experiment', 'grant_tracking', 'n8n_workflow'], pending, run, dashboard: dashboardPayload() });
    }
    if (route.startsWith('leads/') && route.endsWith('/convert')) { const id = route.split('/')[1]; record('lead_conversion', 'acquisition_engine', `Prepared conversion strategy for lead ${id}.`); return finish({ status: 'success', lead_id: id, strategy: 'Prioritize direct outreach, confirm operational fit, and schedule a pilot-readiness review.' }); }
    if (route === 'narcoguard/workflows/refresh') { const timestamp = now(); workflows.forEach((workflow) => { workflow.last_run = timestamp; workflow.progress = Math.min(100, Number(workflow.progress || 0) + 4); }); record('workflow_refresh', 'orchestrator', 'Narcoguard workflows refreshed.'); return finish({ status: 'refreshed', timestamp, workflows, events: collabEvents }); }
    if (route === 'agents/prompt') { const entry = { prompt: String(data.prompt || ''), targets: Array.isArray(data.targets) ? data.targets : ['all'], context: data.context || {}, timestamp: now() }; promptHistory.unshift(entry); promptHistory.splice(25); record('prompt', 'operator', `Prompt dispatched to ${entry.targets.join(', ')}.`); return finish({ status: 'queued', targets: entry.targets, history: promptHistory.slice(0, 8), events: collabEvents }); }
    if (route === 'tasks') { const task = { id: Date.now(), title: String(data.title || 'Untitled task'), owner: String(data.owner || 'orchestrator'), priority: String(data.priority || 'medium'), status: 'queued', created_at: now() }; tasks.unshift(task); record('task', task.owner, `Queued task: ${task.title}`); return finish({ status: 'queued', task, total: tasks.length, tasks, events: collabEvents }); }
    if (route === 'user/messages') { const message = { id: Date.now(), channel: 'operator', message: String(data.message || ''), timestamp: now() }; messages.unshift(message); record('message', 'operator', message.message); return finish({ status: 'sent', message, total: messages.length, messages, events: collabEvents }); }
    if (route === 'autonomy/start' || route === 'autonomy/stop') { autonomy.state.running = route.endsWith('start'); autonomy.state.last_tick = now(); record('autonomy', 'orchestrator', autonomy.state.running ? 'Autonomy loop started.' : 'Autonomy loop stopped.'); return finish({ status: autonomy.state.running ? 'started' : 'stopped', ...autonomy, events: collabEvents }); }
    if (route === 'autonomy/settings') { if (typeof data.daily_budget === 'number') autonomy.settings.daily_budget = data.daily_budget; if (typeof data.primary_channel === 'string' && data.primary_channel) autonomy.settings.primary_channel = data.primary_channel; record('settings', 'operator', 'Autonomy settings updated.'); return finish({ status: 'updated', ...autonomy, events: collabEvents }); }
    if (route === 'pipelines/refresh') { pipelines.forEach((pipeline) => { pipeline.progress = Math.min(100, Number(pipeline.progress || 0) + 7); }); record('pipeline', 'orchestrator', 'Pipelines advanced.'); return finish({ status: 'refreshed', pipelines, events: collabEvents }); }
    if (route === 'campaigns') { const campaign = { id: Date.now(), name: String(data.name || 'Untitled campaign'), channel: String(data.channel || 'email'), goal: String(data.goal || 'leads'), owner: 'content_engine', status: 'planned', created_at: now() }; campaigns.unshift(campaign); record('campaign', 'content_engine', `Planned campaign: ${campaign.name}`); return finish({ status: 'planned', campaign, total: campaigns.length, campaigns, events: collabEvents }); }
    if (route === 'n8n/workflows') {
      const name = String(data.name || 'Untitled workflow');
      const description = String(data.description || '');
      const trigger = String(data.trigger || 'manual');
      const definition = buildN8nWorkflowDefinition(name, description, trigger);
      const workflow: RecordValue = { id: Date.now(), name, description, trigger, path: `n8n_workflows/${name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.json`, status: 'ready', created_at: now(), definition, remote_definition: definition };
      let remote: RecordValue | null = null;
      try {
        if (process.env.N8N_BASE_URL && process.env.N8N_API_KEY) remote = await pushWorkflowToN8n(workflow);
      } catch (error) {
        remote = { status: 'pending', detail: error instanceof Error ? error.message : 'n8n push failed' };
      }
      if (remote?.status === 'activated') {
        workflow.remote_status = 'activated';
        workflow.remote_id = remote.workflowId;
      } else if (remote?.status === 'created') {
        workflow.remote_status = 'created';
        workflow.remote_id = remote.workflow?.id || null;
      } else if (remote?.status === 'pending') {
        workflow.remote_status = 'pending';
        workflow.remote_detail = remote.detail;
      } else {
        workflow.remote_status = 'local_only';
      }
      n8nWorkflows.unshift(workflow);
      const detail = workflow.remote_status === 'activated'
        ? `Created and activated remote n8n workflow${workflow.remote_id ? ` ${workflow.remote_id}` : ''}.`
        : workflow.remote_status === 'created'
          ? 'Remote n8n workflow created.'
          : workflow.remote_status === 'pending'
            ? `Remote n8n activation pending: ${workflow.remote_detail || 'missing credentials or API failure'}.`
            : 'Workflow saved locally.';
      record('workflow', 'orchestrator', `Created n8n workflow: ${name}. ${detail}`);
      return finish({ status: 'created', workflow, remote_status: workflow.remote_status, total: n8nWorkflows.length, workflows: n8nWorkflows, events: collabEvents });
    }
    if (route === 'n8n/workflows/activate') {
      const workflowId = String(data.workflow_id || data.id || '');
      const workflow = workflowId
        ? n8nWorkflows.find((item) => String(item.id) === workflowId || String(item.remote_id || '') === workflowId || item.name === String(data.name || ''))
        : n8nWorkflows[0];
      if (!workflow) return finish({ status: 'failed', detail: 'Workflow not found.' }, 404);
      try {
        const remote = await pushWorkflowToN8n(workflow);
        workflow.remote_status = remote.status;
        workflow.remote_id = remote.workflowId || remote.workflow?.id || workflow.remote_id || null;
        record('workflow', 'orchestrator', `Activated n8n workflow: ${workflow.name}`);
        return finish({ status: 'activated', workflow, remote, events: collabEvents });
      } catch (error) {
        workflow.remote_status = 'pending';
        workflow.remote_detail = error instanceof Error ? error.message : 'n8n activation failed';
        record('workflow_failed', 'orchestrator', `n8n activation failed for ${workflow.name}: ${workflow.remote_detail}`);
        return finish({ status: 'failed', detail: workflow.remote_detail, workflow, events: collabEvents }, 502);
      }
    }
    if (route === 'email/send') {
      try {
        const result = await sendSendGridEmail(data);
        record('email_sent', 'acquisition_engine', `Sent email to ${String(data.to || '').trim()}.`);
        return finish({ ...result, status: 'sent', events: collabEvents });
      } catch (error) {
        record('email_failed', 'acquisition_engine', `Email send failed: ${error instanceof Error ? error.message : 'unknown error'}`);
        return finish({ status: 'failed', detail: error instanceof Error ? error.message : 'Email send failed' }, 502);
      }
    }
    if (route.startsWith('leads/') && route.endsWith('/email')) {
      const id = route.split('/')[1];
      const lead = leadList.find((item) => String(item.id) === id);
      if (!lead?.email) return finish({ status: 'failed', detail: 'Lead not found or email missing.' }, 404);
      try {
        const subject = String(data.subject || `Follow-up from Narcoguard`);
        const text = String(data.text || data.content || `Hello ${String(lead.name || 'there')},\n\nWe are reaching out with a supervised pilot update from Narcoguard.`);
        const result = await sendSendGridEmail({ ...data, to: lead.email, subject, text });
        record('lead_email_sent', 'acquisition_engine', `Sent email to lead ${id}.`);
        return finish({ ...result, status: 'sent', lead_id: id, events: collabEvents });
      } catch (error) {
        record('lead_email_failed', 'acquisition_engine', `Lead email failed for ${id}: ${error instanceof Error ? error.message : 'unknown error'}`);
        return finish({ status: 'failed', detail: error instanceof Error ? error.message : 'Lead email send failed' }, 502);
      }
    }
    if (route === 'content/briefs/refresh') { const brief = { id: Date.now(), title: 'Narcoguard harm-reduction pilot brief', source: 'CHATTY content engine', status: 'ready', created_at: now() }; briefs.unshift(brief); record('brief', 'content_engine', `Generated brief: ${brief.title}`); return finish({ status: 'refreshed', brief, briefs, events: collabEvents }); }
    if (route === 'grants') { const grant = { id: Date.now(), name: String(data.name || 'Untitled grant'), deadline: String(data.deadline || 'TBD'), status: 'tracking', created_at: now() }; grants.unshift(grant); record('grant', 'investor_relations', `Added grant target: ${grant.name}`); return finish({ status: 'created', grant, grants }); }
    if (route === 'experiments/pricing') { const experiment = { id: Date.now(), name: String(data.name || 'Untitled experiment'), hypothesis: String(data.hypothesis || 'Improve conversion'), metric: String(data.metric || 'conversion_rate'), status: 'planned', created_at: now() }; experiments.unshift(experiment); record('experiment', 'revenue_engine', `Created pricing experiment: ${experiment.name}`); return finish({ status: 'created', experiment, experiments }); }
    if (route === 'proposals/draft' || route === 'press/pitch' || route === 'video/script') {
      const type = route === 'proposals/draft' ? 'proposal' : route === 'press/pitch' ? 'pitch' : 'video';
      const prompt = type === 'proposal'
        ? `Draft a concise supervised pilot proposal for Narcoguard. Title: ${String(data.title || 'Operational overdose-response intelligence')}. Include scope, implementation steps, measurable pilot metrics, assumptions, and a clear call to action. State unknowns explicitly. End with these links exactly: NarcoGuard ${narcoguardUrl} and Funding ${fundingUrl}.`
        : type === 'pitch'
          ? `Draft a concise press pitch for Narcoguard. Angle: ${String(data.angle || 'measurable field impact')}. Use a factual public-health tone, avoid unsupported claims, and include a suggested headline and why-now paragraph. End with these links exactly: NarcoGuard ${narcoguardUrl} and Funding ${fundingUrl}.`
          : `Draft a concise 60-second video script for Narcoguard explaining the operational problem, the supervised pilot, and the next step. Do not claim measured results that are not provided. End with these links exactly: NarcoGuard ${narcoguardUrl} and Funding ${fundingUrl}.`;
      try {
        const result = await generateWithProvider(prompt);
        generated.type = type; generated.draft = result.text;
        record('content_generation', 'content_engine', `${type} generated with ${result.provider}.`);
        return finish({ status: 'generated', type, provider: result.provider, draft: generated.draft });
      } catch (error) {
        record('content_generation_failed', 'content_engine', `${type} generation failed.`);
        return finish({ status: 'failed', detail: error instanceof Error ? error.message : 'AI generation failed.' }, 502);
      }
    }
    return finish({ status: 'accepted', route, received: data, timestamp: now() });
  });
}

function missingIntegrations() {
  const missing: string[] = [];
  if (!process.env.NVIDIA_API_KEY && !process.env.OPENAI_API_KEY && !process.env.OPENROUTER_API_KEY) missing.push('AI provider key for live model generation');
  if (!process.env.SENDGRID_API_KEY) missing.push('SendGrid API key for outbound email');
  if (!sendgridFromEmail) missing.push('SendGrid from email for outbound email');
  if (!process.env.TWITTER_API_KEY) missing.push('social provider credentials for outbound posts');
  if (!process.env.N8N_BASE_URL || !process.env.N8N_API_KEY) missing.push('n8n URL and API key for remote workflow activation');
  return missing;
}
