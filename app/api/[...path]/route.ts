import leads from '../../../leads.json';
import youtubeLearningSeed from '../../../generated_content/youtube_learnings.json';

export const runtime = 'edge';

type Lead = { id?: number | string; name?: string; email?: string; source?: string; lead_score?: number; status?: string; created_at?: string; [key: string]: unknown };
type RecordValue = Record<string, any>;
const leadList = leads as Lead[];
const maxAutoFundingRecipients = 8;

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
const fundingRuns: RecordValue[] = [];
const funding = {
  last_run_at: null as string | null,
  last_status: 'idle',
  last_recipients: [] as string[],
  last_package: {
    proposal: '',
    pitch: '',
    email: '',
    social: '',
    grant_notes: '',
    outreach_steps: [] as string[],
  },
  last_summary: '',
};
const youtubeWatchlist: RecordValue[] = [];
const youtubeLearningRuns: RecordValue[] = [];
const youtubeLearning = {
  last_run_at: null as string | null,
  last_status: 'idle',
  last_video_url: '',
  last_video_title: '',
  last_summary: '',
  last_insights: [] as string[],
  learned_count: 0,
};
const pipelines: RecordValue[] = [{ name: 'Revenue Autopilot', status: 'active', progress: 41, stages: [{ name: 'Offer optimization', status: 'active' }, { name: 'Pricing experiments', status: 'queued' }] }];
const autonomy = { state: { running: false, mode: 'production-dashboard', loop_interval_sec: 60, last_tick: null as string | null, last_sweep_at: null as string | null, last_sweep_summary: '' }, settings: { daily_budget: 250, risk_guardrails: 'conservative', primary_channel: 'email' } };
const learning = {
  score: 48,
  last_tick: null as string | null,
  last_signature: '',
  insights: [] as string[],
  recommendations: [] as string[],
  signals: {
    successful_actions: 0,
    failed_actions: 0,
    active_workflows: 0,
    pending_integrations: 0,
  },
};
function buildColeMedinKnowledgeBaseSeed() {
  const entries = Array.isArray(youtubeLearningSeed) ? youtubeLearningSeed : [];
  return entries
    .filter((item) => {
      const text = `${String(item?.title || '')} ${JSON.stringify(item?.insights || {})}`.toLowerCase();
      return ['ai', 'agent', 'code', 'claude', 'archon', 'wiki', 'brain', 'pydantic', 'vercel', 'kimi', 'automation', 'local', 'harness', 'knowledge'].some((needle) => text.includes(needle));
    })
    .map((item) => {
      const insights = item?.insights || {};
      const summary = String(insights.summary || '').trim();
      const keyTopics = Array.isArray(insights.key_topics) ? insights.key_topics.map((value: unknown) => String(value).trim()).filter(Boolean) : [];
      const tips = Array.isArray(insights.actionable_tips) ? insights.actionable_tips.map((value: unknown) => String(value).trim()).filter(Boolean) : [];
      const tools = Array.isArray(insights.tools_mentioned) ? insights.tools_mentioned.map((value: unknown) => String(value).trim()).filter(Boolean) : [];
      const themes = coleMedinThemes({ summary, insights: keyTopics, actions: tips, keywords: tools, title: item?.title });
      return {
        id: `seed-${String(item?.video_id || item?.video_url || item?.title || Date.now())}`,
        title: String(item?.title || 'Cole Medin video'),
        url: String(item?.video_url || ''),
        summary,
        insights: keyTopics,
        actions: tips,
        keywords: tools,
        themes,
        implementation_targets: themes.length ? themes : ['Cole Medin learning'],
        source_run_id: item?.video_id || item?.video_url || item?.title || '',
        learned_at: item?.processed_at || now(),
        updated_at: item?.processed_at || now(),
        seed: true,
      };
    })
    .filter((item) => String(item.url || '').includes('youtube.com/watch'))
    .slice(0, 50);
}
const coleMedinKnowledgeBase: RecordValue[] = buildColeMedinKnowledgeBaseSeed();

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
const stateId = 'global';
const defaultSendgridFromEmail = 'noreply@narcoguard.com';
const sendgridFromEmail = process.env.SENDGRID_FROM_EMAIL || process.env.SENDGRID_FROM || '';
const sendgridFromName = process.env.SENDGRID_FROM_NAME || 'CHATTY';
const resendApiKey = process.env.RESEND_API_KEY || '';
const resendFromEmail = process.env.RESEND_FROM_EMAIL || sendgridFromEmail || defaultSendgridFromEmail;
const resendFromName = process.env.RESEND_FROM_NAME || sendgridFromName || 'CHATTY';
const narcoguardUrl = process.env.NARCOGUARD_URL || 'https://narcoguard-pwa.vercel.app';
const fundingUrl = process.env.NARCOGUARD_FUNDING_URL || process.env.GOFUNDME_URL || 'https://gofund.me/e1a0b3f2';
const coleMedinChannelId = 'UCMwVTLZIRRUyyVrkjDpn4pA';
const coleMedinChannelUrl = 'https://www.youtube.com/@ColeMedin';

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
function parseEmailList(value: unknown) {
  if (Array.isArray(value)) {
    return value.map((item) => String(item || '').trim()).filter((item) => item.includes('@'));
  }
  return String(value || '')
    .split(/[\n,;]/g)
    .map((item) => item.trim())
    .filter((item) => item.includes('@'));
}
function isMissionAlignedProspect(lead: Lead) {
  const haystack = [
    lead.name,
    lead.company,
    lead.source,
    lead.status,
    lead.role,
    lead.metadata && typeof lead.metadata === 'object' ? JSON.stringify(lead.metadata) : '',
  ]
    .map((value) => String(value || '').toLowerCase())
    .join(' ');
  return [
    'health',
    'public',
    'harm reduction',
    'harmreduction',
    'opioid',
    'overdose',
    'naloxone',
    'emergency',
    'ems',
    'first responder',
    'hospital',
    'clinic',
    'recovery',
    'samhsa',
    'cdc',
    'nih',
    'coalition',
    'department of health',
  ].some((keyword) => haystack.includes(keyword));
}
function extractYouTubeVideoId(url: string) {
  const patterns = [
    /(?:v=|youtu\.be\/|embed\/|shorts\/)([a-zA-Z0-9_-]{11})/,
    /^([a-zA-Z0-9_-]{11})$/,
  ];
  for (const pattern of patterns) {
    const match = String(url || '').match(pattern);
    if (match?.[1]) return match[1];
  }
  return '';
}
function isYouTubeUrl(url: string) {
  return /youtube\.com|youtu\.be/i.test(String(url || ''));
}
function decodeXmlEntities(text: string) {
  return String(text || '')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}
function extractFeedEntries(xml: string) {
  const entries: Array<{ title: string; url: string; video_id: string; published: string; updated: string }> = [];
  const entryPattern = /<entry>([\s\S]*?)<\/entry>/g;
  let match: RegExpExecArray | null;
  while ((match = entryPattern.exec(xml))) {
    const entry = match[1];
    const title = decodeXmlEntities((entry.match(/<title>([\s\S]*?)<\/title>/)?.[1] || '').trim());
    const videoId = (entry.match(/<yt:videoId>([\s\S]*?)<\/yt:videoId>/)?.[1] || '').trim();
    const url = (entry.match(/<link[^>]+href="([^"]+)"/)?.[1] || (videoId ? `https://www.youtube.com/watch?v=${videoId}` : '')).trim();
    const published = (entry.match(/<published>([\s\S]*?)<\/published>/)?.[1] || '').trim();
    const updated = (entry.match(/<updated>([\s\S]*?)<\/updated>/)?.[1] || '').trim();
    if (url) {
      entries.push({ title, url, video_id: videoId, published, updated });
    }
  }
  return entries;
}
async function fetchColeMedinFeed(limit = 5) {
  try {
    const response = await fetch(`https://www.youtube.com/feeds/videos.xml?channel_id=${coleMedinChannelId}`, { cache: 'no-store' });
    if (response.ok) {
      const xml = await response.text();
      const entries = extractFeedEntries(xml);
      if (entries.length) {
        return entries.slice(0, limit);
      }
    }
  } catch (error) {
    console.error('Cole Medin feed fetch failed', error);
  }
  try {
    const response = await fetch(`https://www.youtube.com/channel/${coleMedinChannelId}/videos`, { cache: 'no-store' });
    if (!response.ok) return [];
    const html = await response.text();
    const initialDataMatch = html.match(/var ytInitialData = (\{[\s\S]*\});<\/script>/) || html.match(/window\["ytInitialData"\] = (\{[\s\S]*\});/);
    if (!initialDataMatch) return [];
    const data = JSON.parse(initialDataMatch[1]);
    const tabs = data?.contents?.twoColumnBrowseResultsRenderer?.tabs || [];
    const videosTab = tabs.find((tab: RecordValue) => String(tab?.tabRenderer?.title || '') === 'Videos' || Boolean(tab?.tabRenderer?.selected))?.tabRenderer?.content?.richGridRenderer?.contents || [];
    const entries: Array<{ title: string; url: string; video_id: string; published: string; updated: string }> = [];
    for (const item of videosTab) {
      const lockup = item?.richItemRenderer?.content?.lockupViewModel;
      const videoId = String(lockup?.contentId || '').trim();
      const title = String(lockup?.metadata?.lockupMetadataViewModel?.title?.content || '').trim();
      const rowParts = lockup?.metadata?.lockupMetadataViewModel?.metadata?.contentMetadataViewModel?.metadataRows?.[0]?.metadataParts || [];
      const published = String(rowParts?.[1]?.text?.content || rowParts?.[0]?.text?.content || '').trim();
      if (!videoId) continue;
      entries.push({
        title: title || `Cole Medin video ${videoId}`,
        url: `https://www.youtube.com/watch?v=${videoId}`,
        video_id: videoId,
        published,
        updated: published,
      });
      if (entries.length >= limit) break;
    }
    return entries;
  } catch (error) {
    console.error('Cole Medin page fetch failed', error);
    return [];
  }
}
async function fetchYouTubeMetadata(url: string) {
  const videoId = extractYouTubeVideoId(url);
  if (!videoId) {
    return { videoId: '', title: '', description: '', author: '', url };
  }
  const oembedUrl = `https://www.youtube.com/oembed?url=${encodeURIComponent(`https://www.youtube.com/watch?v=${videoId}`)}&format=json`;
  try {
    const response = await fetch(oembedUrl, { cache: 'no-store' });
    if (response.ok) {
      const data = await response.json() as RecordValue;
      return {
        videoId,
        title: String(data.title || ''),
        description: String(data.description || ''),
        author: String(data.author_name || ''),
        thumbnail: String(data.thumbnail_url || ''),
        url: `https://www.youtube.com/watch?v=${videoId}`,
      };
    }
  } catch (error) {
    console.error('YouTube metadata fetch failed', error);
  }
  return { videoId, title: '', description: '', author: '', url: `https://www.youtube.com/watch?v=${videoId}` };
}
async function seedColeMedinWatchlist(limit = 5) {
  const entries = await fetchColeMedinFeed(limit);
  const added: RecordValue[] = [];
  for (const entry of entries) {
    const existing = youtubeWatchlist.find((item) => String(item.url || '') === entry.url);
    if (existing) {
      existing.source = 'cole_medin';
      existing.channel = 'Cole Medin';
      existing.channel_url = coleMedinChannelUrl;
      existing.channel_id = coleMedinChannelId;
      existing.title = existing.title || entry.title;
      continue;
    }
    const watchItem = {
      id: Date.now() + youtubeWatchlist.length,
      url: entry.url,
      title: entry.title,
      video_id: entry.video_id,
      channel: 'Cole Medin',
      channel_url: coleMedinChannelUrl,
      channel_id: coleMedinChannelId,
      source: 'cole_medin',
      created_at: now(),
      learned_at: null as string | null,
      last_summary: '',
    };
    youtubeWatchlist.unshift(watchItem);
    added.push(watchItem);
  }
  if (added.length) {
    record('youtube_watchlist', 'orchestrator', `Seeded ${added.length} Cole Medin video(s) from the channel feed.`);
  }
  return { added, entries, youtube: youtubeStatus() };
}
function applyColeMedinInsights(payload: RecordValue, meta: RecordValue) {
  const text = `${String(payload.summary || '')} ${JSON.stringify(payload.insights || [])} ${JSON.stringify(payload.actions || [])} ${JSON.stringify(payload.keywords || [])}`.toLowerCase();
  const applied: RecordValue[] = [];
  const pushTask = (title: string, detail: string) => {
    tasks.unshift({ id: Date.now() + tasks.length, title, owner: 'orchestrator', priority: 'high', status: 'queued', source: 'cole_medin_learning', detail, created_at: now() });
    applied.push({ type: 'task', title });
  };
  const pushBrief = (title: string, detail: string) => {
    briefs.unshift({ id: Date.now() + briefs.length, title, source: 'Cole Medin learning', status: 'ready', created_at: now(), detail });
    applied.push({ type: 'brief', title });
  };
  const pushWorkflow = (name: string, description: string) => {
    n8nWorkflows.unshift({ id: Date.now() + n8nWorkflows.length, name, description, trigger: 'manual', status: 'ready', source: 'cole_medin_learning', created_at: now() });
    applied.push({ type: 'workflow', name });
  };
  const pushExperiment = (name: string, hypothesis: string) => {
    experiments.unshift({ id: Date.now() + experiments.length, name, hypothesis, metric: 'learning_adoption', status: 'planned', source: 'cole_medin_learning', created_at: now() });
    applied.push({ type: 'experiment', name });
  };

  if (text.includes('agent zero')) {
    pushTask('Implement Agent Zero fleet coordination pattern', 'Cole Medin video emphasized fleet coordination and agent specialization.');
    pushWorkflow('Cole Medin Agent Zero Pattern', 'Turn Cole Medin Agent Zero guidance into a reusable fleet coordination workflow.');
  }
  if (text.includes('archon 2') || text.includes('archon')) {
    pushTask('Apply Archon 2 style orchestration', 'Cole Medin video emphasized hierarchical orchestration and strategic planning.');
    pushBrief('Cole Medin Archon 2 notes', 'Summarize Archon-style orchestration patterns for the CHATTY planner.');
  }
  if (text.includes('bmad')) {
    pushTask('Extend BMAD behavioral modeling', 'Cole Medin video emphasized behavioral modeling and feedback loops.');
    pushExperiment('BMAD learning loop refinement', 'Measure whether behavioral modeling improves automation outcomes.');
  }
  if (text.includes('rag') || text.includes('second brain') || text.includes('context engineering') || text.includes('knowledge base')) {
    pushWorkflow('YouTube knowledge base ingestion', 'Use Cole Medin-style context engineering to improve learning from external content.');
    pushBrief('Context engineering notes', 'Capture Cole Medin context-engineering patterns for reuse in Chatty.');
  }
  if (!applied.length) {
    pushBrief(`Cole Medin video note: ${String(meta.title || 'video')}`, String(payload.summary || 'No explicit implementation notes extracted.'));
  }

  generated.type = 'cole_medin_learning';
  generated.draft = `${String(meta.title || 'Cole Medin video')}\n\n${String(payload.summary || '')}`.trim();
  learning.recommendations = Array.from(new Set([...(payload.actions || []).map((item: unknown) => String(item)), ...(payload.insights || []).map((item: unknown) => String(item)), ...learning.recommendations])).slice(0, 10);
  record('cole_medin_applied', 'orchestrator', `Applied ${applied.length} Cole Medin insight(s) from ${String(meta.title || meta.url || 'video')}.`);
  return applied;
}
async function runColeMedinLearning(limit = 3) {
  const seeded = await seedColeMedinWatchlist(Math.max(limit, 5));
  const targets = youtubeWatchlist.filter((item) => String(item.source || '') === 'cole_medin' && !item.learned_at).slice(0, limit);
  const learned: RecordValue[] = [];
  const applied: RecordValue[] = [];
  const videos = targets.length ? targets : seeded.entries.map((entry) => ({ ...entry, source: 'cole_medin' }));
  for (const video of videos.slice(0, limit)) {
    const result = await runYouTubeLearning([String(video.url || '')], 'cole_medin');
    const details = applyColeMedinInsights(result, video);
    const knowledgeEntry = collectColeMedinKnowledgeBase(result.run || {}, video, details);
    learned.push({ url: video.url, title: video.title || result.run?.video_title || '', summary: result.summary, run: result.run });
    applied.push(...details, { type: 'knowledge_base', title: knowledgeEntry.title, id: knowledgeEntry.id });
    const watched = youtubeWatchlist.find((item) => String(item.url || '') === String(video.url || ''));
    if (watched) {
      watched.learned_at = now();
      watched.last_summary = result.summary;
      watched.last_applied = details.map((item) => item.title || item.name).filter(Boolean);
      watched.knowledge_base_id = knowledgeEntry.id;
    }
  }
  youtubeLearning.last_status = learned.length ? 'cole_medin_learned' : youtubeLearning.last_status;
  youtubeLearning.last_summary = learned.length ? `Cole Medin learning complete for ${learned.length} video(s).` : youtubeLearning.last_summary;
  return {
    status: learned.length ? 'learned' : 'idle',
    summary: youtubeLearning.last_summary || 'No Cole Medin videos processed.',
    learned,
    applied,
    knowledge_base: coleMedinKnowledgeBaseStatus(),
    youtube: youtubeStatus(),
    recent_runs: youtubeLearningRuns,
  };
}
function discoverPotentialRecipients(limit = maxAutoFundingRecipients) {
  const candidates = leadList
    .map((lead) => ({
      lead,
      score: Number(lead.lead_score || 0),
      status: String(lead.status || '').toLowerCase(),
      hasEmail: Boolean(String(lead.email || '').includes('@')),
    }))
    .filter(({ lead, score, status, hasEmail }) => hasEmail && score >= 80 && ['grant_target', 'new', 'engaging', 'qualified', 'warm'].includes(status || '') && Boolean(lead.name || lead.company) && isMissionAlignedProspect(lead));
  candidates.sort((a, b) => {
    const scoreDelta = (b.score || 0) - (a.score || 0);
    if (scoreDelta !== 0) return scoreDelta;
    return String(a.lead.name || a.lead.company || '').localeCompare(String(b.lead.name || b.lead.company || ''));
  });
  return candidates.slice(0, limit).map(({ lead, score }) => ({
    id: lead.id,
    name: lead.name || lead.company || 'Prospect',
    email: String(lead.email || '').trim(),
    source: lead.source || 'lead intelligence',
    lead_score: score,
    status: lead.status || 'qualified',
    created_at: lead.created_at || now(),
  }));
}
function stateSnapshot() { return { workflows, tasks, collabEvents, promptHistory, messages, campaigns, n8nWorkflows, briefs, grants, experiments, pipelines, autonomy, learning, generated, launchRuns, fundingRuns, funding, youtubeWatchlist, youtubeLearningRuns, coleMedinKnowledgeBase, youtubeLearning }; }
function replaceArray(target: RecordValue[], source: unknown) { if (Array.isArray(source)) { target.splice(0, target.length, ...source); } }
function hydrateSnapshot(payload: RecordValue) {
  replaceArray(workflows, payload.workflows); replaceArray(tasks, payload.tasks); replaceArray(collabEvents, payload.collabEvents); replaceArray(promptHistory, payload.promptHistory); replaceArray(messages, payload.messages); replaceArray(campaigns, payload.campaigns); replaceArray(n8nWorkflows, payload.n8nWorkflows); replaceArray(briefs, payload.briefs); replaceArray(grants, payload.grants); replaceArray(experiments, payload.experiments); replaceArray(pipelines, payload.pipelines);
  replaceArray(launchRuns, payload.launchRuns);
  replaceArray(fundingRuns, payload.fundingRuns);
  replaceArray(youtubeWatchlist, payload.youtubeWatchlist);
  replaceArray(youtubeLearningRuns, payload.youtubeLearningRuns);
  replaceArray(coleMedinKnowledgeBase, payload.coleMedinKnowledgeBase);
  if (payload.generated) Object.assign(generated, payload.generated);
  if (payload.autonomy) { Object.assign(autonomy, payload.autonomy); Object.assign(autonomy.state, payload.autonomy.state || {}); Object.assign(autonomy.settings, payload.autonomy.settings || {}); }
  if (payload.funding) {
    Object.assign(funding, payload.funding);
    Object.assign(funding.last_package, payload.funding.last_package || {});
    funding.last_recipients = Array.isArray(payload.funding.last_recipients) ? payload.funding.last_recipients : funding.last_recipients;
  }
  if (payload.youtubeLearning) {
    Object.assign(youtubeLearning, payload.youtubeLearning);
    youtubeLearning.last_insights = Array.isArray(payload.youtubeLearning.last_insights) ? payload.youtubeLearning.last_insights : youtubeLearning.last_insights;
  }
  if (payload.learning) {
    Object.assign(learning, payload.learning);
    Object.assign(learning.signals, payload.learning.signals || {});
    learning.insights = Array.isArray(payload.learning.insights) ? payload.learning.insights : learning.insights;
    learning.recommendations = Array.isArray(payload.learning.recommendations) ? payload.learning.recommendations : learning.recommendations;
  }
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
  const fromEmail = String(payload.from_email || payload.fromEmail || sendgridFromEmail || defaultSendgridFromEmail).trim();
  const fromName = String(payload.from_name || payload.fromName || sendgridFromName || '').trim();
  const replyTo = String(payload.reply_to || payload.replyTo || '').trim();
  if (!to) throw new Error('A recipient email address is required.');
  if (!subject) throw new Error('An email subject is required.');
  if (!text && !html) throw new Error('Email content is required.');
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
async function sendResendEmail(payload: RecordValue) {
  if (!resendApiKey) throw new Error('Resend API key is not configured.');
  const to = String(payload.to || '').trim();
  const subject = String(payload.subject || '').trim();
  const text = String(payload.text || payload.content || '').trim();
  const html = typeof payload.html === 'string' ? payload.html.trim() : '';
  const fromEmail = String(payload.from_email || payload.fromEmail || resendFromEmail).trim();
  const fromName = String(payload.from_name || payload.fromName || resendFromName || '').trim();
  const replyTo = String(payload.reply_to || payload.replyTo || '').trim();
  if (!to) throw new Error('A recipient email address is required.');
  if (!subject) throw new Error('An email subject is required.');
  if (!text && !html) throw new Error('Email content is required.');
  const body: RecordValue = {
    from: fromName ? `${fromName} <${fromEmail}>` : fromEmail,
    to: [to],
    subject,
  };
  if (text) body.text = appendPublicLinks(text);
  if (html) body.html = `${html}<p><a href="${narcoguardUrl}">NarcoGuard</a> · <a href="${fundingUrl}">Funding</a></p>`;
  if (replyTo) body.reply_to = replyTo;

  const response = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${resendApiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });
  const responseText = await response.text();
  let parsed: RecordValue = {};
  try { parsed = responseText ? JSON.parse(responseText) as RecordValue : {}; } catch { parsed = { raw: responseText }; }
  if (!response.ok) throw new Error(String(parsed.message || parsed.error || responseText || `Resend request failed with HTTP ${response.status}.`));
  return { status: 'sent', provider: 'resend', accepted: true, response: parsed.id || parsed.data?.id || responseText || null };
}
async function sendOutboundEmail(payload: RecordValue) {
  const attempts: Array<{ provider: string; run: () => Promise<RecordValue> }> = [];
  if (process.env.SENDGRID_API_KEY) attempts.push({ provider: 'sendgrid', run: () => sendSendGridEmail(payload) });
  if (resendApiKey) attempts.push({ provider: 'resend', run: () => sendResendEmail(payload) });
  if (!attempts.length) throw new Error('No outbound email provider is configured.');

  const failures: string[] = [];
  for (const attempt of attempts) {
    try {
      const result = await attempt.run();
      return { ...result, provider: attempt.provider };
    } catch (error) {
      failures.push(`${attempt.provider}: ${error instanceof Error ? error.message : 'request failed'}`);
    }
  }
  throw new Error(`All outbound email providers failed: ${failures.join('; ')}`);
}
function automationDue(force = false) {
  if (force) return true;
  if (!autonomy.state.running) return false;
  const lastSweep = autonomy.state.last_sweep_at || autonomy.state.last_tick;
  if (!lastSweep) return true;
  const elapsedMs = Date.now() - new Date(lastSweep).getTime();
  const intervalMs = Math.max(15, Number(autonomy.state.loop_interval_sec || 60)) * 1000;
  return elapsedMs >= intervalMs;
}
async function runAutomationCycle(trigger = 'dashboard', force = false) {
  const actions: string[] = [];
  if (!automationDue(force)) {
    return { ran: false, trigger, actions, summary: 'Automation cycle skipped because the next interval is not due yet.' };
  }

  const timestamp = now();
  autonomy.state.last_sweep_at = timestamp;
  autonomy.state.last_tick = timestamp;

  workflows.forEach((workflow) => {
    if (String(workflow.status || '').toLowerCase() === 'active') {
      workflow.progress = Math.min(100, Number(workflow.progress || 0) + 2);
      workflow.last_run = timestamp;
    }
  });
  if (workflows.length) actions.push(`Advanced ${workflows.length} workflow(s).`);

  pipelines.forEach((pipeline) => {
    pipeline.progress = Math.min(100, Number(pipeline.progress || 0) + 3);
  });
  if (pipelines.length) actions.push(`Advanced ${pipelines.length} pipeline(s).`);

  campaigns.forEach((campaign) => {
    if (String(campaign.status || '').toLowerCase() === 'planned') campaign.status = 'active';
  });
  if (campaigns.length) actions.push('Activated planned campaign(s).');

  const nextYouTube = youtubeWatchlist.find((item) => !item.learned_at && isYouTubeUrl(String(item.url || '')));
  if (nextYouTube) {
    try {
      const youtubeResult = await runYouTubeLearning([String(nextYouTube.url || '')], trigger);
      nextYouTube.learned_at = timestamp;
      nextYouTube.last_summary = youtubeResult.summary;
      actions.push(`Learned from YouTube: ${String(nextYouTube.url || '')}`);
    } catch (error) {
      nextYouTube.last_error = error instanceof Error ? error.message : 'YouTube learning failed';
      actions.push(`YouTube learning failed for ${String(nextYouTube.url || '')}.`);
    }
  }

  const coleMedinAutoEnabled = String(process.env.CHATTY_COLE_MEDIN_AUTO || 'true').toLowerCase() !== 'false';
  if (coleMedinAutoEnabled) {
    try {
      const coleResult = await runColeMedinLearning(1);
      if (coleResult.learned?.length) {
        actions.push(`Learned from Cole Medin channel: ${String(coleResult.learned[0]?.title || coleResult.learned[0]?.url || 'video')}.`);
      }
    } catch (error) {
      actions.push(`Cole Medin learning failed: ${error instanceof Error ? error.message : 'unknown error'}.`);
    }
  }

  if (n8nWorkflows.length && process.env.N8N_BASE_URL && process.env.N8N_API_KEY) {
    const remoteCandidate = n8nWorkflows.find((workflow) => !workflow.remote_status || workflow.remote_status === 'local_only' || workflow.remote_status === 'pending') || n8nWorkflows[0];
    if (remoteCandidate) {
      try {
        const remote = await pushWorkflowToN8n(remoteCandidate);
        remoteCandidate.remote_status = remote.status;
        remoteCandidate.remote_id = remote.workflowId || remote.workflow?.id || remoteCandidate.remote_id || null;
        actions.push(`Activated n8n workflow ${String(remoteCandidate.name || remoteCandidate.id)}.`);
      } catch (error) {
        remoteCandidate.remote_status = 'pending';
        remoteCandidate.remote_detail = error instanceof Error ? error.message : 'n8n automation failed';
        actions.push(`n8n activation failed for ${String(remoteCandidate.name || remoteCandidate.id)}.`);
      }
    }
  }

  const notifyEmail = String(process.env.AUTOMATION_NOTIFY_EMAIL || process.env.OPS_NOTIFY_EMAIL || process.env.ADMIN_EMAIL || '').trim();
  if (notifyEmail && (process.env.SENDGRID_API_KEY || resendApiKey)) {
    const summary = `CHATTY automation cycle complete.\n\nWorkflows: ${workflows.length}\nPipelines: ${pipelines.length}\nCampaigns: ${campaigns.length}\nPending integrations: ${missingIntegrations().join('; ') || 'none'}\n\n${publicLinksFooter()}`;
    try {
      const emailResult = await sendOutboundEmail({ to: notifyEmail, subject: 'CHATTY automation cycle summary', text: summary });
      actions.push(`Sent automation summary email via ${String(emailResult.provider || 'email')}.`);
    } catch (error) {
      actions.push(`Automation summary email failed: ${error instanceof Error ? error.message : 'unknown error'}.`);
    }
  }

  if (process.env.NVIDIA_API_KEY || process.env.OPENAI_API_KEY || process.env.OPENROUTER_API_KEY || process.env.XAI_API_KEY || process.env.MISTRAL_API_KEY || process.env.DEEPSEEK_API_KEY) {
    try {
      const result = await generateWithProvider(
        `Write a concise automation status note for CHATTY using only these live facts: workflows=${workflows.length}, campaigns=${campaigns.length}, tasks=${tasks.length}, pending_integrations=${missingIntegrations().join('; ') || 'none'}, public_narcoguard=${narcoguardUrl}, funding=${fundingUrl}. Do not invent outcomes.`
      );
      generated.type = 'automation-summary';
      generated.draft = result.text;
      actions.push(`Generated live automation summary with ${result.provider}.`);
    } catch (error) {
      actions.push(`Automation summary generation failed: ${error instanceof Error ? error.message : 'unknown error'}.`);
    }
  }

  const learningState = learnFromSignals(trigger);
  autonomy.state.last_sweep_summary = actions.length ? actions.join(' ') : 'Automation cycle completed with no eligible actions.';
  record('automation_sweep', 'orchestrator', autonomy.state.last_sweep_summary);
  return { ran: true, trigger, timestamp, actions, learning: learningState, summary: autonomy.state.last_sweep_summary };
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
function clamp(value: number, min: number, max: number) { return Math.min(max, Math.max(min, value)); }
function summarizeSignals() {
  const recentEvents = collabEvents.slice(0, 12);
  const failedActions = recentEvents.filter((event) => /fail|error|blocked/i.test(String(event.event || '') + ' ' + String(event.detail || ''))).length;
  const successfulActions = recentEvents.filter((event) => /sent|launched|activated|generated|refreshed|queued|completed/i.test(String(event.event || '') + ' ' + String(event.detail || ''))).length;
  const activeWorkflows = workflows.filter((workflow) => String(workflow.status || '').toLowerCase() === 'active').length + n8nWorkflows.filter((workflow) => String(workflow.remote_status || workflow.status || '').toLowerCase() === 'activated').length;
  const pendingIntegrations = missingIntegrations().length;
  const busyTasks = tasks.filter((task) => ['active', 'queued', 'pending'].includes(String(task.status || '').toLowerCase())).length;
  const averageWorkflowProgress = workflows.length
    ? Math.round(workflows.reduce((sum, workflow) => sum + Number(workflow.progress || 0), 0) / workflows.length)
    : 0;
  const score = clamp(
    35 +
      successfulActions * 5 +
      activeWorkflows * 4 +
      Math.min(15, averageWorkflowProgress / 5) +
      Math.min(10, campaigns.length * 2) +
      Math.min(10, n8nWorkflows.length * 2) -
      failedActions * 7 -
      pendingIntegrations * 5 -
      Math.max(0, busyTasks - workflows.length),
    0,
    100,
  );

  const insights = [
    activeWorkflows ? `${activeWorkflows} workflow${activeWorkflows === 1 ? '' : 's'} are active.` : 'No active workflows were detected.',
    successfulActions ? `${successfulActions} recent action${successfulActions === 1 ? '' : 's'} completed successfully.` : 'No recent successful actions were recorded.',
    pendingIntegrations ? `${pendingIntegrations} integration${pendingIntegrations === 1 ? '' : 's'} still need credentials or credits.` : 'All tracked integrations are currently satisfied.',
    averageWorkflowProgress ? `Average workflow progress is ${averageWorkflowProgress}%.` : 'Workflow progress is not yet established.',
  ].filter(Boolean).slice(0, 4);

  const recommendations: string[] = [];
  if (pendingIntegrations) recommendations.push(`Connect the missing integrations: ${missingIntegrations().join('; ')}.`);
  if (failedActions) recommendations.push('Review the latest failed actions and retry the blocked automations.');
  if (!n8nWorkflows.length) recommendations.push('Create or activate at least one n8n workflow so the automation layer can run outside the dashboard.');
  if (!campaigns.length) recommendations.push('Seed a live campaign so learning has a conversion signal to optimize.');
  if (!generated.draft) recommendations.push('Generate a fresh proposal, pitch, or video script to keep outbound content current.');

  return {
    score,
    insights,
    recommendations: recommendations.slice(0, 4),
    signals: {
      successful_actions: successfulActions,
      failed_actions: failedActions,
      active_workflows: activeWorkflows,
      pending_integrations: pendingIntegrations,
    },
  };
}
function learnFromSignals(trigger = 'heartbeat') {
  const previousSignature = learning.last_signature;
  const signature = JSON.stringify({
    workflows: workflows.map((workflow) => [workflow.id, workflow.status, workflow.progress, workflow.last_run]),
    tasks: tasks.map((task) => [task.id, task.status, task.owner]),
    collab: collabEvents.slice(0, 12).map((event) => [event.event, event.agent, event.detail]),
    campaigns: campaigns.map((campaign) => [campaign.id, campaign.status, campaign.channel]),
    n8n: n8nWorkflows.map((workflow) => [workflow.id, workflow.remote_status || workflow.status, workflow.remote_id || null]),
    generated: [generated.type || '', String(generated.draft || '').length],
    youtube: [youtubeLearning.learned_count, youtubeLearning.last_video_title || '', String(youtubeLearning.last_summary || '').length],
    autonomy: [autonomy.state.running, autonomy.state.mode, autonomy.settings.primary_channel, autonomy.settings.daily_budget],
    missing: missingIntegrations(),
  });
  const snapshot = summarizeSignals();
  learning.score = snapshot.score;
  learning.insights = snapshot.insights;
  learning.recommendations = snapshot.recommendations;
  learning.signals = snapshot.signals;
  if (youtubeLearning.last_summary) {
    learning.recommendations = Array.from(new Set([youtubeLearning.last_summary, ...learning.recommendations])).slice(0, 6);
  }
  learning.last_tick = now();
  learning.last_signature = signature;
  if (trigger !== 'hydrate' && signature !== previousSignature) {
    record('learning_update', 'orchestrator', `Learning loop updated to ${learning.score}% confidence.`);
  }
  return learning;
}
function fundingStatus() {
  const autoRecipients = discoverPotentialRecipients();
  return {
    ready: Boolean(funding.last_package.proposal || funding.last_package.pitch || funding.last_recipients.length || fundingRuns.length),
    last_run_at: funding.last_run_at,
    last_status: funding.last_status,
    last_recipients: funding.last_recipients,
    last_recipient_source: funding.last_recipients.length ? (funding.last_recipients.every((recipient) => autoRecipients.some((item) => item.email === recipient)) ? 'auto' : 'manual') : 'none',
    contacts_configured: funding.last_recipients.length > 0,
    package_ready: Boolean(funding.last_package.proposal || funding.last_package.pitch || funding.last_package.email),
    runs: fundingRuns.length,
    auto_discovery_ready: autoRecipients.length > 0,
    potential_recipients: autoRecipients,
    public_links: {
      narcoguard: narcoguardUrl,
      funding: fundingUrl,
    },
  };
}
function coleMedinThemes(payload: RecordValue) {
  const text = `${String(payload.summary || '')} ${JSON.stringify(payload.insights || [])} ${JSON.stringify(payload.actions || [])} ${JSON.stringify(payload.keywords || [])}`.toLowerCase();
  return [
    ['agent zero', 'Agent Zero coordination'],
    ['archon', 'Archon orchestration'],
    ['bmad', 'BMAD modeling'],
    ['second brain', 'Second brain / knowledge base'],
    ['knowledge base', 'Knowledge base ingestion'],
    ['rag', 'Retrieval augmented generation'],
    ['local ai', 'Local AI deployment'],
    ['npm install', 'One-click install'],
    ['claude code', 'Claude Code workflow'],
    ['outreach', 'Outreach automation'],
    ['workflow', 'Workflow automation'],
    ['automation', 'Automation'],
  ]
    .filter(([needle]) => text.includes(needle))
    .map(([, theme]) => theme);
}
function coleMedinKnowledgeBaseStatus() {
  const themes = new Map<string, number>();
  for (const entry of coleMedinKnowledgeBase) {
    for (const theme of Array.isArray(entry.themes) ? entry.themes : []) {
      themes.set(theme, (themes.get(theme) || 0) + 1);
    }
  }
  return {
    total: coleMedinKnowledgeBase.length,
    themes: Array.from(themes.entries()).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([theme, count]) => ({ theme, count })),
    recent: coleMedinKnowledgeBase.slice(0, 5),
  };
}
function collectColeMedinKnowledgeBase(run: RecordValue, video: RecordValue, applied: RecordValue[]) {
  const themes = coleMedinThemes(run);
  const implementationTargets = applied.map((item) => item.title || item.name || item.type).filter(Boolean);
  const entry = {
    id: `cole-${video.video_id || run.id || Date.now()}`,
    title: String(video.title || run.video_title || 'Cole Medin video'),
    url: String(video.url || run.video_url || ''),
    summary: String(run.summary || ''),
    insights: Array.isArray(run.insights) ? run.insights : [],
    actions: Array.isArray(run.actions) ? run.actions : [],
    keywords: Array.isArray(run.keywords) ? run.keywords : [],
    themes,
    implementation_targets: implementationTargets,
    source_run_id: run.id,
    learned_at: now(),
    updated_at: now(),
  };
  const existingIndex = coleMedinKnowledgeBase.findIndex((item) => String(item.url || '') === entry.url || String(item.id || '') === entry.id);
  if (existingIndex >= 0) {
    coleMedinKnowledgeBase.splice(existingIndex, 1, { ...coleMedinKnowledgeBase[existingIndex], ...entry });
  } else {
    coleMedinKnowledgeBase.unshift(entry);
  }
  coleMedinKnowledgeBase.splice(50);
  record('cole_medin_knowledge_base', 'orchestrator', `Updated Cole Medin knowledge base with ${entry.title}.`);
  return entry;
}
function youtubeStatus() {
  return {
    last_run_at: youtubeLearning.last_run_at,
    last_status: youtubeLearning.last_status,
    last_video_url: youtubeLearning.last_video_url,
    last_video_title: youtubeLearning.last_video_title,
    last_summary: youtubeLearning.last_summary,
    last_insights: youtubeLearning.last_insights,
    learned_count: youtubeLearning.learned_count,
    watchlist_count: youtubeWatchlist.length,
    watchlist: youtubeWatchlist.slice(0, 10),
    cole_medin: {
      channel: coleMedinChannelUrl,
      channel_id: coleMedinChannelId,
      seeded_videos: youtubeWatchlist.filter((item) => String(item.source || '') === 'cole_medin').length,
      learned_videos: youtubeWatchlist.filter((item) => String(item.source || '') === 'cole_medin' && Boolean(item.learned_at)).length,
      pending_videos: youtubeWatchlist.filter((item) => String(item.source || '') === 'cole_medin' && !item.learned_at).slice(0, 5),
      knowledge_base: coleMedinKnowledgeBaseStatus(),
    },
  };
}
async function runYouTubeLearning(urls: string[] = [], trigger = 'manual') {
  const queue = urls.length ? urls : youtubeWatchlist.map((item) => String(item.url || item.video_url || '')).filter(Boolean);
  if (!queue.length) {
    return { status: 'idle', summary: 'No YouTube URLs available.', youtube: youtubeStatus(), runs: youtubeLearningRuns };
  }
  const url = queue[0];
  if (!isYouTubeUrl(url)) {
    throw new Error('A valid YouTube URL is required.');
  }
  const timestamp = now();
  const meta = await fetchYouTubeMetadata(url);
  const prompt = `Learn from this YouTube video for CHATTY automation improvements.
Title: ${meta.title || 'Unknown title'}
Author: ${meta.author || 'Unknown author'}
Description: ${meta.description || 'No description available.'}
URL: ${meta.url}

Return strict JSON with keys: summary, insights, actions, keywords.
Focus on concrete automation, learning, outreach, and workflow improvements.
Do not invent transcript details that are not in the metadata.`;
  const result = await generateWithProvider(prompt);
  let payload: RecordValue = {};
  try {
    payload = JSON.parse(result.text);
  } catch {
    payload = { summary: result.text, insights: [], actions: [], keywords: [] };
  }

  const summary = String(payload.summary || result.text || '').trim();
  const insights = Array.isArray(payload.insights) ? payload.insights.map((item) => String(item).trim()).filter(Boolean) : [];
  const actions = Array.isArray(payload.actions) ? payload.actions.map((item) => String(item).trim()).filter(Boolean) : [];
  const keywords = Array.isArray(payload.keywords) ? payload.keywords.map((item) => String(item).trim()).filter(Boolean) : [];

  youtubeLearning.last_run_at = timestamp;
  youtubeLearning.last_status = 'learned';
  youtubeLearning.last_video_url = meta.url;
  youtubeLearning.last_video_title = meta.title || url;
  youtubeLearning.last_summary = summary;
  youtubeLearning.last_insights = insights;
  youtubeLearning.learned_count += 1;

  const run = {
    id: Date.now(),
    trigger,
    video_url: meta.url,
    video_title: meta.title || url,
    author: meta.author || '',
    summary,
    insights,
    actions,
    keywords,
    created_at: timestamp,
  };
  youtubeLearningRuns.unshift(run);
  youtubeLearningRuns.splice(20);

  record('youtube_learning', 'orchestrator', `Learned from YouTube: ${meta.title || url}`);
  return {
    status: 'learned',
    summary,
    run,
    youtube: youtubeStatus(),
    recent_runs: youtubeLearningRuns,
  };
}
async function runFundingCampaign(trigger = 'manual', options: RecordValue = {}) {
  const manualRecipients = parseEmailList(options.recipients || process.env.FUNDING_OUTREACH_EMAILS || '');
  const autoRecipients = manualRecipients.length ? [] : discoverPotentialRecipients();
  const recipients = manualRecipients.length ? manualRecipients : autoRecipients.map((item) => item.email);
  const recipientSource = manualRecipients.length ? 'manual' : recipients.length ? 'auto_discovered' : 'none';
  const notifyEmail = String(options.notify_email || process.env.FUNDING_NOTIFY_EMAIL || process.env.ADMIN_EMAIL || '').trim();
  const sendNow = options.send_now !== false;
  const timestamp = now();

  const packagePrompt = `Return strict JSON with keys proposal, pitch, email, social, grant_notes, outreach_steps.
Use only these live facts: NarcoGuard is hosted at ${narcoguardUrl}. Funding page: ${fundingUrl}.
Keep the tone factual and concise. Do not invent metrics, awards, or results.
The package is for overdose-prevention funding, pilot deployment, and mission-aligned partner outreach.
Include a grant/pilot-partner email draft, a short pitch, a proposal summary, and a social post.
`;

  const result = await generateWithProvider(packagePrompt);
  let packageData: RecordValue = {};
  try {
    packageData = JSON.parse(result.text);
  } catch {
    packageData = {
      proposal: result.text,
      pitch: result.text,
      email: result.text,
      social: result.text,
      grant_notes: '',
      outreach_steps: [],
    };
  }

  const proposal = String(packageData.proposal || result.text || '').trim();
  const pitch = String(packageData.pitch || proposal).trim();
  const emailDraft = String(packageData.email || proposal).trim();
  const socialDraft = String(packageData.social || pitch).trim();

  funding.last_run_at = timestamp;
  funding.last_status = 'drafted';
  funding.last_recipients = recipients;
  funding.last_package = {
    proposal,
    pitch,
    email: emailDraft,
    social: socialDraft,
    grant_notes: String(packageData.grant_notes || '').trim(),
    outreach_steps: Array.isArray(packageData.outreach_steps) ? packageData.outreach_steps : [],
  };

  const campaign = {
    id: Date.now(),
    name: 'NarcoGuard Pilot Partner Outreach',
    channel: recipients.length ? 'pilot-outreach' : 'grant-writing',
    goal: 'funding',
    owner: 'investor_relations',
    status: recipients.length ? 'active' : 'planned',
    created_at: timestamp,
    recipient_source: recipientSource,
  };
  campaigns.unshift(campaign);
  grants.unshift({
    id: Date.now() + 1,
    name: 'Narcoguard pilot outreach package',
    deadline: 'TBD',
    status: 'tracking',
    created_at: timestamp,
  });
  briefs.unshift({
    id: Date.now() + 2,
    title: 'Narcoguard pilot outreach package',
    source: 'CHATTY investor relations',
    status: 'ready',
    created_at: timestamp,
  });
  n8nWorkflows.unshift({
    id: Date.now() + 3,
    name: 'Narcoguard Funding Outreach Workflow',
    description: 'Generate and distribute grant and pilot-partner materials, track responses, and log follow-ups.',
    trigger: 'manual',
    status: 'ready',
    created_at: timestamp,
  });

  const sendResults: RecordValue[] = [];
  if (sendNow && recipients.length) {
    for (const recipient of recipients) {
      try {
        const message = `Narcoguard funding package:\n\n${emailDraft}\n\nProposal:\n${proposal}\n\nPitch:\n${pitch}\n\nSocial:\n${socialDraft}\n\n${publicLinksFooter()}`;
        const sent = await sendOutboundEmail({
          to: recipient,
          subject: 'Narcoguard funding package',
          text: message,
        });
        sendResults.push({ recipient, status: 'sent', provider: sent.provider });
      } catch (error) {
        sendResults.push({ recipient, status: 'failed', error: error instanceof Error ? error.message : 'send failed' });
      }
    }
    funding.last_status = sendResults.some((item) => item.status === 'sent') ? 'sent' : 'drafted';
  } else if (notifyEmail) {
    try {
      const summary = `Funding package drafted for Narcoguard.\n\nRecipients: ${recipients.length ? recipients.join(', ') : 'none'}\n\nProposal:\n${proposal}\n\nPitch:\n${pitch}\n\n${publicLinksFooter()}`;
      const sent = await sendOutboundEmail({
        to: notifyEmail,
        subject: 'Narcoguard funding package drafted',
        text: summary,
      });
      sendResults.push({ recipient: notifyEmail, status: 'sent', provider: sent.provider, role: 'notify' });
      funding.last_status = 'sent';
    } catch (error) {
      sendResults.push({ recipient: notifyEmail, status: 'failed', error: error instanceof Error ? error.message : 'notify failed', role: 'notify' });
    }
  }

  if (!sendNow && !notifyEmail) {
    funding.last_status = 'drafted';
  } else if (sendResults.some((item) => item.status === 'sent')) {
    funding.last_status = 'sent';
  }

  const run = {
    id: Date.now(),
    trigger,
    status: funding.last_status,
    recipients,
    recipient_source: recipientSource,
    send_now: sendNow,
    campaign_id: campaign.id,
    package: funding.last_package,
    send_results: sendResults,
    created_at: timestamp,
  };
  fundingRuns.unshift(run);
  fundingRuns.splice(20);

  const summary = recipients.length
    ? `Pilot outreach drafted for ${recipients.length} recipient(s) via ${recipientSource}.`
    : 'Pilot outreach package drafted and queued for review.';
  funding.last_summary = summary;
  record('funding_campaign', 'investor_relations', summary);
  return {
    status: funding.last_status,
    summary,
    run,
    campaign,
    grants,
    briefs,
    workflows: n8nWorkflows,
    package: funding.last_package,
    send_results: sendResults,
    recipient_source: recipientSource,
    funding: fundingStatus(),
  };
}
function governanceStatus() {
  const emailReady = Boolean(process.env.SENDGRID_API_KEY || resendApiKey);
  const executorReady = Boolean(
    process.env.N8N_BASE_URL && process.env.N8N_API_KEY
    || emailReady
    || Boolean(process.env.TWITTER_API_KEY)
  );
  const recentFailures = collabEvents
    .slice(0, 20)
    .filter((event) => /fail|error|blocked/i.test(`${String(event.event || '')} ${String(event.detail || '')}`));
  const recentSweeps = collabEvents
    .slice(0, 20)
    .filter((event) => event.event === 'automation_sweep');
  return {
    planner: {
      name: 'Archon2',
      branch: 'planner',
      ready: Boolean(agents.length && workflows.length),
      source: 'hierarchical task decomposition',
      active_coordinators: agents.filter((agent) => ['orchestrator', 'revenue_engine', 'content_engine', 'investor_relations'].includes(agent.name)).length,
      guidance: learning.recommendations[0] || 'Use Archon2 to break work into delegated subtasks.',
    },
    executor: {
      name: 'n8n + providers',
      branch: 'executor',
      ready: executorReady,
      n8n_ready: Boolean(process.env.N8N_BASE_URL && process.env.N8N_API_KEY),
      email_ready: emailReady,
      social_ready: Boolean(process.env.TWITTER_API_KEY),
      active_workflows: n8nWorkflows.length,
      guidance: executorReady ? 'Execution paths available.' : 'Connect at least one execution provider.',
    },
    oversight: {
      name: 'BMAD',
      branch: 'oversight',
      ready: true,
      source: 'behavioral modeling and validation',
      validation_checks: [
        'transparency logging',
        'learning loop score',
        'failure detection',
        'integration readiness',
      ],
      recent_failures: recentFailures.length,
      recent_sweeps: recentSweeps.length,
      guidance: recentFailures.length ? 'Review recent failures before expanding automation.' : 'Oversight layer is clear.',
    },
    balance_score: clamp(
      30 +
      (Boolean(agents.length && workflows.length) ? 20 : 0) +
      (executorReady ? 25 : 0) +
      (recentFailures.length ? -recentFailures.length * 5 : 10) +
      (recentSweeps.length ? 5 : 0),
      0,
      100,
    ),
  };
}
function leadsPayload() { const publicLeads = leadList.map(publicLead); return { total: publicLeads.length, new: publicLeads.filter((lead) => (lead.status || 'new') === 'new').length, leads: publicLeads }; }
function prospectsPayload() { return { total: discoverPotentialRecipients().length, prospects: discoverPotentialRecipients(), timestamp: now() }; }
function weeklyPayload() { return { completed: collabEvents, events: collabEvents, summary: `Narcoguard automation is operational. ${campaigns.length} campaign(s), ${tasks.length} task(s), and ${messages.length} operator message(s) tracked.` }; }
function integrationStatus() {
  const emailReady = Boolean(process.env.SENDGRID_API_KEY || resendApiKey);
  return {
    public_links: {
      narcoguard: narcoguardUrl,
      funding: fundingUrl,
    },
    email: {
      configured: emailReady,
      ready: emailReady,
      primary: process.env.SENDGRID_API_KEY ? 'sendgrid' : resendApiKey ? 'resend' : null,
      fallbacks: [
        process.env.SENDGRID_API_KEY ? 'sendgrid' : null,
        resendApiKey ? 'resend' : null,
      ].filter(Boolean),
    },
    sendgrid: {
      configured: Boolean(process.env.SENDGRID_API_KEY),
      from_email_configured: Boolean(sendgridFromEmail || defaultSendgridFromEmail),
      ready: Boolean(process.env.SENDGRID_API_KEY),
    },
    resend: {
      configured: Boolean(resendApiKey),
      from_email_configured: Boolean(resendFromEmail),
      ready: Boolean(resendApiKey),
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
  learnFromSignals('dashboard');
  return { status: { status: 'running', systems_active: agents.length, total_automations: workflows.length, uptime_hours: 0, revenue_generated: 0 }, leads: leadsPayload(), workflows: { workflows }, agents: { agents }, tasks: { total: tasks.length, tasks }, collab: { total: collabEvents.length, events: collabEvents }, messages: { total: messages.length, messages }, autonomy, learning, governance: governanceStatus(), funding: fundingStatus(), youtube: youtubeStatus(), pipelines: { pipelines }, campaigns: { total: campaigns.length, campaigns }, n8n: { total: n8nWorkflows.length, workflows: n8nWorkflows }, transparency: { completed: collabEvents }, briefs: { briefs }, content: { briefs }, grants: { grants }, experiments: { experiments }, generated, integrations: integrationStatus(), anomalies: { anomalies: [] }, kpi: { anomalies: [] }, weekly: weeklyPayload(), weekly_brief: weeklyPayload(), timestamp: now() };
}
function getPayload(path: string[]) {
  switch (path.join('/')) {
    case 'dashboard/all': return dashboardPayload(); case 'leads': return leadsPayload(); case 'leads/prospects': return prospectsPayload(); case 'learning/status': return { learning: learnFromSignals('status'), youtube: youtubeStatus(), timestamp: now() }; case 'automation/status': return { autonomy, learning: learnFromSignals('status'), governance: governanceStatus(), funding: fundingStatus(), youtube: youtubeStatus(), timestamp: now() }; case 'governance/status': return { governance: governanceStatus(), timestamp: now() }; case 'funding/status': return { funding: fundingStatus(), funding_runs: fundingRuns, timestamp: now() }; case 'youtube/status': return { youtube: youtubeStatus(), recent_runs: youtubeLearningRuns, timestamp: now() }; case 'youtube/cole-medin/status': return { youtube: youtubeStatus(), knowledge_base: coleMedinKnowledgeBaseStatus(), recent_runs: youtubeLearningRuns.filter((run) => String(run.trigger || '').includes('cole')), timestamp: now() }; case 'youtube/cole-medin/knowledge-base': return { knowledge_base: coleMedinKnowledgeBaseStatus(), youtube: youtubeStatus(), timestamp: now() }; case 'narcoguard/workflows': return { project: 'Narcoguard', workflows }; case 'narcoguard/launch/status': return { latest: launchRuns[0] || null, runs: launchRuns, events: collabEvents }; case 'agents': return { total: agents.length, agents }; case 'tasks': return { total: tasks.length, tasks }; case 'agents/collab': return { total: collabEvents.length, events: collabEvents }; case 'user/messages': return { total: messages.length, messages }; case 'autonomy/status': return autonomy; case 'pipelines': return { pipelines }; case 'campaigns': return { total: campaigns.length, campaigns }; case 'n8n/workflows': return { total: n8nWorkflows.length, workflows: n8nWorkflows }; case 'integrations/status': return integrationStatus(); case 'transparency/report': return { completed: collabEvents }; case 'content/briefs': return { briefs }; case 'grants': return { grants }; case 'experiments/pricing': return { experiments }; case 'kpi/anomalies': return { anomalies: [] }; case 'weekly/brief': return weeklyPayload(); default: return { status: 'ok', route: path.join('/') };
  }
}
async function body(request: Request): Promise<RecordValue> { try { return await request.json() as RecordValue; } catch { return {}; } }

export function GET(_request: Request, context: { params: Promise<{ path: string[] }> }) { return context.params.then(async ({ path }) => { await hydrateFromSupabase(); return json(getPayload(path)); }); }

export function POST(request: Request, context: { params: Promise<{ path: string[] }> }) {
  return context.params.then(async ({ path }) => {
    const route = path.join('/'); const data = await body(request);
    await hydrateFromSupabase();
    const finish = async (payload: unknown, status = 200) => { learnFromSignals(route); await persistToSupabase(); return json(payload, status); };
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
    if (route === 'automation/sweep') {
      const result = await runAutomationCycle('manual', Boolean(data.force));
      return finish({ status: result.ran ? 'completed' : 'skipped', ...result, dashboard: await dashboardPayload(), events: collabEvents });
    }
    if (route === 'youtube/cole-medin/seed') {
      try {
        const result = await seedColeMedinWatchlist(Number(data.limit || 5));
        return finish({ status: 'seeded', ...result, dashboard: await dashboardPayload(), events: collabEvents });
      } catch (error) {
        record('youtube_cole_medin_failed', 'orchestrator', `Cole Medin seeding failed: ${error instanceof Error ? error.message : 'unknown error'}`);
        return finish({ status: 'failed', detail: error instanceof Error ? error.message : 'Cole Medin seeding failed' }, 502);
      }
    }
    if (route === 'youtube/cole-medin/run') {
      try {
        const result = await runColeMedinLearning(Number(data.limit || 3));
        return finish({ ...result, dashboard: await dashboardPayload(), events: collabEvents });
      } catch (error) {
        record('youtube_cole_medin_failed', 'orchestrator', `Cole Medin learning failed: ${error instanceof Error ? error.message : 'unknown error'}`);
        return finish({ status: 'failed', detail: error instanceof Error ? error.message : 'Cole Medin learning failed' }, 502);
      }
    }
    if (route === 'youtube/watchlist') {
      const urls = Array.isArray(data.urls) ? data.urls : [data.url].filter(Boolean);
      const added = urls
        .map((url) => String(url || '').trim())
        .filter(Boolean)
        .filter((url) => isYouTubeUrl(url))
        .map((url) => {
          const existing = youtubeWatchlist.find((item) => String(item.url || '') === url);
          if (existing) return existing;
          const entry = { id: Date.now() + youtubeWatchlist.length, url, created_at: now(), learned_at: null, last_summary: '' };
          youtubeWatchlist.unshift(entry);
          return entry;
        });
      if (!added.length) return finish({ status: 'failed', detail: 'No valid YouTube URLs supplied.' }, 400);
      record('youtube_watchlist', 'orchestrator', `Added ${added.length} YouTube URL(s) to the watchlist.`);
      return finish({ status: 'added', added, youtube: youtubeStatus(), dashboard: await dashboardPayload() });
    }
    if (route === 'youtube/learn') {
      try {
        const urls = Array.isArray(data.urls) ? data.urls.map((item) => String(item || '').trim()).filter(Boolean) : [String(data.url || '').trim()].filter(Boolean);
        const result = await runYouTubeLearning(urls, 'manual');
        return finish({ ...result, dashboard: await dashboardPayload(), events: collabEvents });
      } catch (error) {
        record('youtube_learning_failed', 'orchestrator', `YouTube learning failed: ${error instanceof Error ? error.message : 'unknown error'}`);
        return finish({ status: 'failed', detail: error instanceof Error ? error.message : 'YouTube learning failed' }, 502);
      }
    }
    if (route === 'autonomy/settings') { if (typeof data.daily_budget === 'number') autonomy.settings.daily_budget = data.daily_budget; if (typeof data.primary_channel === 'string' && data.primary_channel) autonomy.settings.primary_channel = data.primary_channel; record('settings', 'operator', 'Autonomy settings updated.'); return finish({ status: 'updated', ...autonomy, events: collabEvents }); }
    if (route === 'funding/run') {
      try {
        const result = await runFundingCampaign('manual', {
          recipients: data.recipients,
          notify_email: data.notify_email,
          send_now: data.send_now,
        });
        return finish({ ...result, dashboard: await dashboardPayload(), events: collabEvents });
      } catch (error) {
        record('funding_failed', 'investor_relations', `Funding campaign failed: ${error instanceof Error ? error.message : 'unknown error'}`);
        return finish({ status: 'failed', detail: error instanceof Error ? error.message : 'Funding campaign failed' }, 502);
      }
    }
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
        const result = await sendOutboundEmail(data);
        record('email_sent', 'acquisition_engine', `Sent email to ${String(data.to || '').trim()} via ${String(result.provider || 'email')}.`);
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
        const result = await sendOutboundEmail({ ...data, to: lead.email, subject, text });
        record('lead_email_sent', 'acquisition_engine', `Sent email to lead ${id} via ${String(result.provider || 'email')}.`);
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
  if (!process.env.SENDGRID_API_KEY && !resendApiKey) missing.push('SendGrid or Resend API key for outbound email');
  if (!process.env.TWITTER_API_KEY) missing.push('social provider credentials for outbound posts');
  if (!process.env.N8N_BASE_URL || !process.env.N8N_API_KEY) missing.push('n8n URL and API key for remote workflow activation');
  return missing;
}
