/**
 * app.js — 小说 AI Agent 聊天驱动 UI
 *
 * 聊天为主要交互界面，右侧显示当前故事状态。
 */

// ===================== State ===================== //
const state = {
  currentStoryId: null,
  currentStory: null,
  stories: [],
  messages: [],
  isProcessing: false,
  panelOpen: true,
};

// ===================== DOM Refs ===================== //
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];

const dom = {};

function initDomRefs() {
  dom.storySelector = $('#story-selector');
  dom.btnNewStory = $('#btn-new-story');
  dom.btnTogglePanel = $('#btn-toggle-panel');
  dom.btnClosePanel = $('#btn-close-panel');
  dom.chatMessages = $('#chat-messages');
  dom.chatInput = $('#chat-input');
  dom.btnSend = $('#btn-send');
  dom.storyPanel = $('#story-panel');
  dom.panelBody = $('#panel-body');
  dom.panelEmpty = $('#panel-empty');
  dom.panelContent = $('#panel-content');
  dom.panelStoryTitle = $('#panel-story-title');
  dom.panelOutline = $('#panel-outline');
  dom.panelChars = $('#panel-chars');
  dom.panelSettings = $('#panel-settings');
  dom.panelChapters = $('#panel-chapters');
  dom.btnGenOutline = $('#btn-gen-outline');
  dom.btnAddChar = $('#btn-add-char');
  dom.btnAddSetting = $('#btn-add-setting');
  dom.btnNewChapter = $('#btn-new-chapter');

  // Modal
  dom.modalOverlay = $('#modal-overlay');
  dom.modalTitle = $('#modal-title');
  dom.modalBody = $('#modal-body');
  dom.btnModalConfirm = $('#btn-modal-confirm');
}

// ===================== API Client ===================== //
const API_BASE = '/api';

async function api(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const config = {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  };
  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body);
  }
  const resp = await fetch(url, config);
  if (!resp.ok) {
    let msg = `HTTP ${resp.status}`;
    try {
      const err = await resp.json();
      msg = err.detail || msg;
    } catch (_) {}
    throw new Error(msg);
  }
  // 204 No Content
  if (resp.status === 204) return null;
  return resp.json();
}

// ===================== Toast ===================== //
function showToast(msg, type = 'error') {
  const existing = $('.toast');
  if (existing) existing.remove();

  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

// ===================== Modal ===================== //
let modalResolve = null;

function openModal(title, bodyHtml) {
  dom.modalTitle.textContent = title;
  dom.modalBody.innerHTML = bodyHtml;
  dom.modalOverlay.classList.remove('hidden');
  return new Promise((resolve) => {
    modalResolve = resolve;
  });
}

function closeModal() {
  dom.modalOverlay.classList.add('hidden');
  if (modalResolve) {
    modalResolve(null);
    modalResolve = null;
  }
}

// Modal events
dom.modalOverlay.addEventListener('click', (e) => {
  if (e.target === dom.modalOverlay) closeModal();
});

dom.btnModalConfirm.addEventListener('click', () => {
  // Collect form data from modal-body
  const formData = {};
  const inputs = $$('input, textarea, select', dom.modalBody);
  inputs.forEach((inp) => {
    if (inp.name) formData[inp.name] = inp.value;
  });
  closeModal();
  if (modalResolve) {
    modalResolve(formData);
    modalResolve = null;
  }
});

// ===================== Message Rendering ===================== //
function addMessage(role, content, extras = {}) {
  const msg = { role, content, ...extras };
  state.messages.push(msg);
  renderMessage(msg);
  scrollChatBottom();
  return msg;
}

function renderMessage(msg) {
  const container = dom.chatMessages;

  // Remove thinking indicator if present
  const thinking = $('.msg-thinking');
  if (thinking) thinking.remove();

  const div = document.createElement('div');
  div.className = `msg msg-${msg.role === 'user' ? 'user' : 'ai'}`;

  if (msg.role === 'user') {
    div.innerHTML = `
      <div class="msg-avatar">我</div>
      <div class="msg-bubble">${escapeHtml(msg.content)}</div>
    `;
  } else {
    div.innerHTML = `
      <div class="msg-avatar">🪄</div>
      <div class="msg-bubble">${renderAiContent(msg)}</div>
    `;
  }

  container.appendChild(div);
}

function renderAiContent(msg) {
  let html = '';
  // Main text content
  if (msg.content) {
    html += `<p>${escapeHtml(msg.content).replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>')}</p>`;
  }

  // Rich cards
  if (msg.cards) {
    msg.cards.forEach((card) => {
      html += renderRichCard(card);
    });
  }

  // Suggestions
  if (msg.suggestions && msg.suggestions.length) {
    html += `<div class="rich-card-actions">`;
    msg.suggestions.forEach((s) => {
      html += `<button class="btn-tag" data-action="${s.action}" data-payload='${escapeHtml(JSON.stringify(s.payload || {}))}'>${escapeHtml(s.label)}</button>`;
    });
    html += `</div>`;
  }

  return html;
}

function renderRichCard(card) {
  const typeClass = card.type === 'outline' ? 'card-outline'
    : card.type === 'character' ? 'card-character'
    : card.type === 'setting' ? 'card-setting'
    : card.type === 'chapter' ? 'card-chapter'
    : '';

  let actionsHtml = '';
  if (card.actions && card.actions.length) {
    actionsHtml = `<div class="rich-card-actions">`;
    card.actions.forEach((a) => {
      actionsHtml += `<button class="btn-tag" data-action="${a.action}" data-payload='${escapeHtml(JSON.stringify(a.payload || {}))}'>${escapeHtml(a.label)}</button>`;
    });
    actionsHtml += `</div>`;
  }

  return `
    <div class="rich-card ${typeClass}">
      ${card.title ? `<div class="rich-card-header">${escapeHtml(card.title)}</div>` : ''}
      <div class="rich-card-body">${escapeHtml(card.body).replace(/\n/g, '<br>')}</div>
      ${actionsHtml}
    </div>
  `;
}

function showThinking() {
  const container = dom.chatMessages;
  const div = document.createElement('div');
  div.className = 'msg msg-thinking';
  div.innerHTML = `
    <div class="msg-avatar">🪄</div>
    <div class="msg-bubble">
      <div class="thinking-dots">
        <span></span><span></span><span></span>
      </div>
    </div>
  `;
  container.appendChild(div);
  scrollChatBottom();
}

function scrollChatBottom() {
  dom.chatMessages.scrollTop = dom.chatMessages.scrollHeight;
}

// ===================== Chat Actions (Delegation) ===================== //
// Click delegation for suggestion/card buttons
dom.chatMessages.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-action]');
  if (!btn) return;

  let payload = {};
  try {
    payload = JSON.parse(btn.dataset.payload || '{}');
  } catch (_) {}

  const action = btn.dataset.action;
  handleAction(action, payload);
});

async function handleAction(action, payload) {
  try {
    switch (action) {
      case 'apply-outline':
        await applyOutline(payload);
        break;
      case 'save-chapter':
        await saveChapter(payload);
        break;
      case 'save-character':
        await saveCharacter(payload);
        break;
      case 'save-setting':
        await saveSetting(payload);
        break;
      case 'load-chapter':
        await loadChapterForEdit(payload);
        break;
      case 'delete-item':
        await deleteStoryItem(payload);
        break;
      default:
        showToast(`未知操作: ${action}`);
    }
  } catch (err) {
    showToast(`操作失败: ${err.message}`);
  }
}

// ===================== Story Data Operations ===================== //
async function loadStories() {
  try {
    state.stories = await api('/stories');
    renderStorySelector();
  } catch (err) {
    showToast(`加载故事列表失败: ${err.message}`);
  }
}

function renderStorySelector() {
  const sel = dom.storySelector;
  sel.innerHTML = '<option value="">— 选择故事 —</option>';
  state.stories.forEach((s) => {
    const opt = document.createElement('option');
    opt.value = s.id;
    opt.textContent = s.title;
    if (s.id === state.currentStoryId) opt.selected = true;
    sel.appendChild(opt);
  });
}

async function selectStory(storyId) {
  if (!storyId) {
    state.currentStoryId = null;
    state.currentStory = null;
    renderStoryPanel();
    return;
  }

  try {
    state.currentStoryId = storyId;
    state.currentStory = await api(`/stories/${storyId}`);
    renderStorySelector();
    renderStoryPanel();

    // Add a system message showing the story was loaded
    addMessage('ai', `已加载故事「${state.currentStory.title}」`, {
      suggestions: [
        { label: '生成大纲', action: 'gen-outline', payload: {} },
        { label: '写第一章', action: 'write-chapter', payload: {} },
      ],
    });
  } catch (err) {
    showToast(`加载故事失败: ${err.message}`);
  }
}

async function createStory(title, genre, description) {
  try {
    const story = await api('/stories', {
      method: 'POST',
      body: { title, genre, description },
    });
    state.stories.push(story);
    renderStorySelector();
    await selectStory(story.id);

    addMessage('ai', `🎉 已创建新故事「${title}」！接下来你想做什么？`, {
      suggestions: [
        { label: '生成大纲', action: 'gen-outline', payload: {} },
        { label: '添加人物', action: 'add-character', payload: {} },
        { label: '添加设定', action: 'add-setting', payload: {} },
      ],
    });
    return story;
  } catch (err) {
    showToast(`创建故事失败: ${err.message}`);
  }
}

async function deleteStory(storyId) {
  if (!confirm('确定要删除这个故事吗？此操作不可撤销。')) return;
  try {
    await api(`/stories/${storyId}`, { method: 'DELETE' });
    state.stories = state.stories.filter((s) => s.id !== storyId);
    if (state.currentStoryId === storyId) {
      state.currentStoryId = null;
      state.currentStory = null;
    }
    renderStorySelector();
    renderStoryPanel();
    addMessage('ai', '故事已删除。');
  } catch (err) {
    showToast(`删除失败: ${err.message}`);
  }
}

// ===================== Story Panel Rendering ===================== //
function renderStoryPanel() {
  const story = state.currentStory;
  if (!story) {
    dom.panelEmpty.classList.remove('hidden');
    dom.panelContent.classList.add('hidden');
    return;
  }

  dom.panelEmpty.classList.add('hidden');
  dom.panelContent.classList.remove('hidden');

  // Title
  dom.panelStoryTitle.textContent = story.title;

  // Genre & desc in a small meta row
  const metaHtml = [];
  if (story.genre) metaHtml.push(`类型: ${story.genre}`);
  if (story.description) metaHtml.push(story.description);
  // We'll put this in the title area
  dom.panelStoryTitle.title = metaHtml.join(' · ');

  // Outline
  dom.panelOutline.textContent = story.outline || '暂无大纲';

  // Characters
  const chars = story.characters || [];
  if (chars.length === 0) {
    dom.panelChars.innerHTML = '<div class="panel-item" style="color:var(--text-muted);font-size:12px;justify-content:center;">暂无人物</div>';
  } else {
    dom.panelChars.innerHTML = chars
      .map(
        (c, i) => `
      <div class="panel-item">
        <span class="item-name">${escapeHtml(c.name)}</span>
        <span class="item-desc">${escapeHtml(c.role || c.traits || '')}</span>
        <button class="item-del" data-action="delete-item" data-payload='${escapeHtml(JSON.stringify({ type: 'character', id: c.id || i }))}' title="删除">✕</button>
      </div>`
      )
      .join('');
  }

  // Settings
  const settings = story.settings || [];
  if (settings.length === 0) {
    dom.panelSettings.innerHTML = '<div class="panel-item" style="color:var(--text-muted);font-size:12px;justify-content:center;">暂无设定</div>';
  } else {
    dom.panelSettings.innerHTML = settings
      .map(
        (s, i) => `
      <div class="panel-item">
        <span class="item-name">${escapeHtml(s.name)}</span>
        <span class="item-desc">${escapeHtml(s.description || '')}</span>
        <button class="item-del" data-action="delete-item" data-payload='${escapeHtml(JSON.stringify({ type: 'setting', id: s.id || i }))}' title="删除">✕</button>
      </div>`
      )
      .join('');
  }

  // Chapters
  const chapters = story.chapters || [];
  if (chapters.length === 0) {
    dom.panelChapters.innerHTML = '<div class="panel-item" style="color:var(--text-muted);font-size:12px;justify-content:center;">暂无章节</div>';
  } else {
    dom.panelChapters.innerHTML = chapters
      .map(
        (ch, i) => `
      <div class="panel-item chapter-item" data-action="load-chapter" data-payload='${escapeHtml(JSON.stringify({ storyId: story.id, chapterId: ch.id }))}'>
        <span class="item-name">${escapeHtml(ch.title || `第${ch.chapter_number || i + 1}章`)}</span>
        <span class="item-desc">${ch.content ? (ch.content.length + '字') : '空'}</span>
        <button class="item-del" data-action="delete-item" data-payload='${escapeHtml(JSON.stringify({ type: 'chapter', id: ch.id, storyId: story.id }))}' title="删除">✕</button>
      </div>`
      )
      .join('');
  }
}

// ===================== Delete items from panel ===================== //
async function deleteStoryItem(payload) {
  const { type, id, storyId } = payload;
  const sid = storyId || state.currentStoryId;
  if (!sid || id === undefined) return;

  if (!confirm(`确定删除此${type === 'character' ? '人物' : type === 'setting' ? '设定' : '章节'}吗？`)) return;

  try {
    if (type === 'character') {
      await api(`/stories/${sid}/characters/${id}`, { method: 'DELETE' });
    } else if (type === 'setting') {
      await api(`/stories/${sid}/settings/${id}`, { method: 'DELETE' });
    } else if (type === 'chapter') {
      await api(`/stories/${sid}/chapters/${id}`, { method: 'DELETE' });
    }
    // Reload story
    await refreshCurrentStory();
    addMessage('ai', '已删除。');
  } catch (err) {
    showToast(`删除失败: ${err.message}`);
  }
}

// ===================== Refresh Story ===================== //
async function refreshCurrentStory() {
  if (!state.currentStoryId) return;
  try {
    state.currentStory = await api(`/stories/${state.currentStoryId}`);
    renderStoryPanel();
  } catch (err) {
    showToast(`刷新故事失败: ${err.message}`);
  }
}

// ===================== AI Actions ===================== //
async function generateOutlineAction(instructions) {
  if (!state.currentStoryId) {
    showToast('请先选择或创建一个故事');
    return;
  }

  showThinking();
  try {
    const result = await api('/agent/generate-outline', {
      method: 'POST',
      body: { story_id: state.currentStoryId, instructions },
    });

    const outlineText = result.outline || result.content || result;

    addMessage('ai', '📋 我为你生成了故事大纲：', {
      cards: [
        {
          type: 'outline',
          title: '📋 故事大纲',
          body: typeof outlineText === 'string' ? outlineText : JSON.stringify(outlineText, null, 2),
          actions: [{ label: '✅ 应用此大纲', action: 'apply-outline', payload: { outline: typeof outlineText === 'string' ? outlineText : JSON.stringify(outlineText, null, 2) } }],
        },
      ],
      suggestions: [
        { label: '写第一章', action: 'write-chapter', payload: {} },
        { label: '重新生成', action: 'gen-outline', payload: {} },
      ],
    });

    await refreshCurrentStory();
  } catch (err) {
    addMessage('ai', `❌ 生成失败: ${err.message}`);
  }
}

async function applyOutline(payload) {
  if (!state.currentStoryId) return;
  try {
    await api(`/stories/${state.currentStoryId}`, {
      method: 'PUT',
      body: { outline: payload.outline },
    });
    await refreshCurrentStory();
    addMessage('ai', '✅ 大纲已保存！');
  } catch (err) {
    showToast(`保存大纲失败: ${err.message}`);
  }
}

async function writeChapterAction(title, summary) {
  if (!state.currentStoryId) {
    showToast('请先选择或创建一个故事');
    return;
  }

  showThinking();
  try {
    const result = await api('/agent/write-chapter', {
      method: 'POST',
      body: { story_id: state.currentStoryId, chapter_title: title, chapter_summary: summary || '' },
    });

    const chapterContent = result.content || result;

    addMessage('ai', `✍️ 已写好「${title || '新章节'}」：`, {
      cards: [
        {
          type: 'chapter',
          title: `📖 ${title || '新章节'}`,
          body: typeof chapterContent === 'string' ? chapterContent.slice(0, 600) + '...' : JSON.stringify(chapterContent, null, 2).slice(0, 600) + '...',
          actions: [{ label: '💾 保存此章节', action: 'save-chapter', payload: { title: title || '新章节', content: typeof chapterContent === 'string' ? chapterContent : JSON.stringify(chapterContent, null, 2) } }],
        },
      ],
      suggestions: [
        { label: '续写下一章', action: 'continue-chapter', payload: {} },
        { label: '重新写', action: 'write-chapter', payload: {} },
      ],
    });
  } catch (err) {
    addMessage('ai', `❌ 写作失败: ${err.message}`);
  }
}

async function saveChapter(payload) {
  if (!state.currentStoryId) return;
  try {
    await api(`/stories/${state.currentStoryId}/chapters`, {
      method: 'POST',
      body: { title: payload.title || '新章节', content: payload.content },
    });
    await refreshCurrentStory();
    addMessage('ai', `✅ 「${payload.title || '新章节'}」已保存到故事中！`);
  } catch (err) {
    showToast(`保存章节失败: ${err.message}`);
  }
}

async function continueChapterAction() {
  if (!state.currentStoryId) {
    showToast('请先选择或创建一个故事');
    return;
  }

  const story = state.currentStory;
  const chapters = story.chapters || [];
  if (chapters.length === 0) {
    addMessage('ai', '还没有章节可以续写。请先写第一章！');
    return;
  }

  // Use the last chapter's content
  const lastCh = chapters[chapters.length - 1];
  if (!lastCh.content) {
    addMessage('ai', '上一章内容为空，无法续写。');
    return;
  }

  showThinking();
  try {
    const result = await api('/agent/continue', {
      method: 'POST',
      body: { story_id: state.currentStoryId },
    });

    const chapterContent = result.content || result;

    const nextChapterNum = (lastCh.chapter_number || chapters.length) + 1;
    const title = `第${nextChapterNum}章`;

    addMessage('ai', `📖 续写完成：`, {
      cards: [
        {
          type: 'chapter',
          title: `📖 ${title}`,
          body: typeof chapterContent === 'string' ? chapterContent.slice(0, 600) + '...' : JSON.stringify(chapterContent, null, 2).slice(0, 600) + '...',
          actions: [{ label: '💾 保存此章节', action: 'save-chapter', payload: { title, content: typeof chapterContent === 'string' ? chapterContent : JSON.stringify(chapterContent, null, 2) } }],
        },
      ],
      suggestions: [
        { label: '再续写一章', action: 'continue-chapter', payload: {} },
      ],
    });
  } catch (err) {
    addMessage('ai', `❌ 续写失败: ${err.message}`);
  }
}

async function rewriteChapterAction(chapterId, instructions) {
  if (!state.currentStoryId) {
    showToast('请先选择或创建一个故事');
    return;
  }

  if (!chapterId) {
    // Prompt user to select a chapter
    addMessage('ai', '请在右侧面板中点击要改写的章节，然后再试。');
    return;
  }

  showThinking();
  try {
    const result = await api('/agent/rewrite', {
      method: 'POST',
      body: { story_id: state.currentStoryId, chapter_id: chapterId, instructions },
    });

    const rewrittenContent = result.content || result;

    addMessage('ai', '✏️ 改写完成：', {
      cards: [
        {
          type: 'chapter',
          title: '📖 改写结果',
          body: typeof rewrittenContent === 'string' ? rewrittenContent.slice(0, 600) + '...' : JSON.stringify(rewrittenContent, null, 2).slice(0, 600) + '...',
          actions: [{ label: '💾 保存改写', action: 'save-chapter', payload: { title: '改写版', content: typeof rewrittenContent === 'string' ? rewrittenContent : JSON.stringify(rewrittenContent, null, 2) } }],
        },
      ],
    });
  } catch (err) {
    addMessage('ai', `❌ 改写失败: ${err.message}`);
  }
}

async function expandChapterAction(chapterId) {
  if (!state.currentStoryId) {
    showToast('请先选择或创建一个故事');
    return;
  }

  if (!chapterId) {
    addMessage('ai', '请在右侧面板中点击要扩写的章节，然后再试。');
    return;
  }

  showThinking();
  try {
    const result = await api('/agent/expand', {
      method: 'POST',
      body: { story_id: state.currentStoryId, chapter_id: chapterId },
    });

    const expandedContent = result.content || result;

    addMessage('ai', '📝 扩写完成：', {
      cards: [
        {
          type: 'chapter',
          title: '📖 扩写结果',
          body: typeof expandedContent === 'string' ? expandedContent.slice(0, 600) + '...' : JSON.stringify(expandedContent, null, 2).slice(0, 600) + '...',
          actions: [{ label: '💾 保存扩写', action: 'save-chapter', payload: { title: '扩写版', content: typeof expandedContent === 'string' ? expandedContent : JSON.stringify(expandedContent, null, 2) } }],
        },
      ],
    });
  } catch (err) {
    addMessage('ai', `❌ 扩写失败: ${err.message}`);
  }
}

async function chatWithAgent(message) {
  showThinking();
  try {
    const result = await api('/agent/chat', {
      method: 'POST',
      body: { message },
    });

    const reply = result.reply || result.content || result;
    addMessage('ai', typeof reply === 'string' ? reply : JSON.stringify(reply, null, 2), {
      suggestions: [
        { label: '生成大纲', action: 'gen-outline', payload: {} },
        { label: '写章节', action: 'write-chapter', payload: {} },
        { label: '咨询趋势', action: 'chat-trend', payload: {} },
      ],
    });
  } catch (err) {
    addMessage('ai', `❌ 对话失败: ${err.message}`);
  }
}

// ===================== Intent Detection ===================== //
function detectIntent(text) {
  const t = text.toLowerCase();

  // Generate outline
  if (/^(生成|给我|帮我|写一个?)(.*)(大纲|世界观|设定)/.test(t) ||
      /生成大纲/.test(t) ||
      /大纲/.test(t) && /生成|写|创建|做/.test(t)) {
    return { action: 'gen-outline', params: { instructions: text } };
  }

  // Write chapter
  if (/(写|写一?章|写第|创作|生成第|生成一?章)/.test(t) && /章/.test(t)) {
    // Extract chapter title if possible
    let title = '';
    let summary = '';
    if (/["""]([^"""]+)["""]/.test(text)) {
      title = RegExp.$1;
    } else if (/第(.+)章/.test(text)) {
      title = text.match(/第(.+)章/)[0];
    } else {
      title = '新章节';
    }
    // Everything after 是/内容/关于 could be summary
    if (/(?:内容|关于|是)(.+)/.test(text)) {
      summary = RegExp.$1.trim();
    }
    return { action: 'write-chapter', params: { title, summary } };
  }

  // Continue / 续写
  if (/续写|继续|下一章|接/.test(t)) {
    return { action: 'continue-chapter', params: {} };
  }

  // Rewrite
  if (/(改写|重写|修改|润色)/.test(t)) {
    return { action: 'rewrite-chapter', params: { instructions: text } };
  }

  // Expand
  if (/(扩写|扩充|展开|丰富)/.test(t)) {
    return { action: 'expand-chapter', params: {} };
  }

  // Trends / Chat
  if (/(趋势|热门|推荐题材|什么题材|流行|平台|创作建议|咨询)/.test(t)) {
    return { action: 'chat', params: { message: text } };
  }

  // Create story
  if (/(新建|创建|新书|开新坑|写一本|想写)/.test(t)) {
    return { action: 'create-story', params: { text } };
  }

  // Default: chat
  return { action: 'chat', params: { message: text } };
}

// ===================== Process User Message ===================== //
async function processUserMessage(text) {
  if (!text.trim()) return;
  if (state.isProcessing) return;

  state.isProcessing = true;
  dom.btnSend.disabled = true;

  // Add user message
  addMessage('user', text);

  // Detect intent
  const intent = detectIntent(text);
  console.log('[Intent]', intent);

  try {
    switch (intent.action) {
      case 'gen-outline':
        await generateOutlineAction(intent.params.instructions);
        break;
      case 'write-chapter':
        await writeChapterAction(intent.params.title, intent.params.summary);
        break;
      case 'continue-chapter':
        await continueChapterAction();
        break;
      case 'rewrite-chapter':
        await rewriteChapterAction(null, intent.params.instructions);
        break;
      case 'expand-chapter':
        await expandChapterAction(null);
        break;
      case 'create-story':
        // Show the new story modal
        showNewStoryModal(intent.params.text);
        break;
      case 'chat':
      default:
        await chatWithAgent(text);
        break;
    }
  } catch (err) {
    addMessage('ai', `❌ 处理消息时出错: ${err.message}`);
  } finally {
    state.isProcessing = false;
    dom.btnSend.disabled = false;
    dom.chatInput.focus();
  }
}

// ===================== Chat Input ===================== //
function sendMessage() {
  const text = dom.chatInput.value.trim();
  if (!text) return;
  dom.chatInput.value = '';
  dom.chatInput.style.height = 'auto';
  processUserMessage(text);
}

// ===================== Modal: New Story ===================== //
function showNewStoryModal(hintText) {
  // Try to extract title and genre from hint text
  let defaultTitle = '';
  let defaultGenre = '';

  if (hintText) {
    const t = hintText;
    // Extract title from quotes
    if (/["""]([^"""]+)["""]/.test(t)) {
      defaultTitle = RegExp.$1;
    }
    // Extract genre keywords
    const genres = ['玄幻', '仙侠', '都市', '科幻', '悬疑', '言情', '历史', '奇幻', '武侠', '恐怖', '游戏', '体育'];
    for (const g of genres) {
      if (t.includes(g)) {
        defaultGenre = g;
        break;
      }
    }
    // If no explicit title, use the first meaningful phrase
    if (!defaultTitle) {
      const match = t.match(/(?:写一本|想写|写个?)(.+?)(?:小说|故事|书)?$/);
      if (match) defaultTitle = match[1].trim();
    }
  }

  const html = `
    <label>故事名称</label>
    <input type="text" name="title" value="${escapeHtml(defaultTitle)}" placeholder="输入故事名称" autofocus>
    <label>类型（可选）</label>
    <input type="text" name="genre" value="${escapeHtml(defaultGenre)}" placeholder="如：玄幻、仙侠、都市、科幻...">
    <label>简介（可选）</label>
    <textarea name="description" rows="3" placeholder="简单描述你的故事..."></textarea>
  `;

  openModal('新建故事', html).then((data) => {
    if (data && data.title) {
      createStory(data.title, data.genre || '', data.description || '');
    }
  });
}

// ===================== Modal: Add Character ===================== //
function showAddCharacterModal() {
  if (!state.currentStoryId) {
    showToast('请先选择或创建一个故事');
    return;
  }

  const html = `
    <label>人物名称</label>
    <input type="text" name="name" placeholder="输入人物名称" autofocus>
    <label>角色定位</label>
    <input type="text" name="role" placeholder="如：男主角、女主角、反派…">
    <label>性格/特征</label>
    <textarea name="traits" rows="2" placeholder="性格特点、外貌特征、能力…"></textarea>
    <label>背景故事</label>
    <textarea name="background" rows="3" placeholder="身世、经历…"></textarea>
  `;

  openModal('添加人物', html).then(async (data) => {
    if (data && data.name) {
      try {
        await api(`/stories/${state.currentStoryId}/characters`, {
          method: 'POST',
          body: { name: data.name, role: data.role || '', traits: data.traits || '', background: data.background || '' },
        });
        await refreshCurrentStory();
        addMessage('ai', `✅ 已添加人物「${data.name}」`);
      } catch (err) {
        showToast(`添加人物失败: ${err.message}`);
      }
    }
  });
}

// ===================== Modal: Add Setting ===================== //
function showAddSettingModal() {
  if (!state.currentStoryId) {
    showToast('请先选择或创建一个故事');
    return;
  }

  const html = `
    <label>设定名称</label>
    <input type="text" name="name" placeholder="如：修炼体系、魔法等级、国家势力…" autofocus>
    <label>描述</label>
    <textarea name="description" rows="4" placeholder="详细描述这个设定…"></textarea>
  `;

  openModal('添加设定', html).then(async (data) => {
    if (data && data.name) {
      try {
        await api(`/stories/${state.currentStoryId}/settings`, {
          method: 'POST',
          body: { name: data.name, description: data.description || '' },
        });
        await refreshCurrentStory();
        addMessage('ai', `✅ 已添加设定「${data.name}」`);
      } catch (err) {
        showToast(`添加设定失败: ${err.message}`);
      }
    }
  });
}

// ===================== Modal: New Chapter ===================== //
function showNewChapterModal() {
  if (!state.currentStoryId) {
    showToast('请先选择或创建一个故事');
    return;
  }

  const chapters = state.currentStory?.chapters || [];
  const nextNum = chapters.length + 1;

  const html = `
    <label>章节标题</label>
    <input type="text" name="title" value="第${nextNum}章" autofocus>
    <label>章节内容（可留空让 AI 生成）</label>
    <textarea name="content" rows="6" placeholder="可直接粘贴内容，或留空后点击确定让 AI 生成..."></textarea>
  `;

  openModal('新建章节', html).then(async (data) => {
    if (data && data.title) {
      if (data.content) {
        // Manual save
        try {
          await api(`/stories/${state.currentStoryId}/chapters`, {
            method: 'POST',
            body: { title: data.title, content: data.content },
          });
          await refreshCurrentStory();
          addMessage('ai', `✅ 章节「${data.title}」已保存`);
        } catch (err) {
          showToast(`保存章节失败: ${err.message}`);
        }
      } else {
        // No content - offer AI generation
        addMessage('ai', `要为「${data.title}」生成内容吗？`, {
          suggestions: [
            { label: '✍️ 让 AI 写作', action: 'write-chapter', payload: { title: data.title } },
          ],
        });
      }
    }
  });
}

// ===================== Load Chapter for Edit/View ===================== //
async function loadChapterForEdit(payload) {
  const { storyId, chapterId } = payload;
  if (!storyId || !chapterId) return;

  try {
    const chapter = await api(`/stories/${storyId}/chapters/${chapterId}`);

    const contentPreview = chapter.content ? chapter.content.slice(0, 500) : '（空）';

    addMessage('ai', `📖 ${chapter.title || '章节'}`, {
      cards: [
        {
          type: 'chapter',
          title: `📖 ${chapter.title || '章节'}`,
          body: contentPreview + (chapter.content && chapter.content.length > 500 ? '...' : ''),
          actions: [
            { label: '✏️ 改写', action: 'rewrite-trigger', payload: { chapterId } },
            { label: '📝 扩写', action: 'expand-trigger', payload: { chapterId } },
          ],
        },
      ],
    });
  } catch (err) {
    showToast(`加载章节失败: ${err.message}`);
  }
}

// ===================== Event Listeners ===================== //
function setupEventListeners() {
  // Story selector
  dom.storySelector.addEventListener('change', (e) => {
    selectStory(e.target.value);
  });

  // New story button
  dom.btnNewStory.addEventListener('click', () => {
    showNewStoryModal('');
  });

  // Toggle panel
  dom.btnTogglePanel.addEventListener('click', () => {
    state.panelOpen = !state.panelOpen;
    dom.storyPanel.classList.toggle('panel-closed', !state.panelOpen);
  });

  dom.btnClosePanel.addEventListener('click', () => {
    state.panelOpen = false;
    dom.storyPanel.classList.add('panel-closed');
  });

  // Send message
  dom.btnSend.addEventListener('click', sendMessage);

  // Chat input: Enter to send, Shift+Enter for newline
  dom.chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Auto-resize textarea
  dom.chatInput.addEventListener('input', () => {
    dom.chatInput.style.height = 'auto';
    dom.chatInput.style.height = Math.min(dom.chatInput.scrollHeight, 120) + 'px';
  });

  // Panel action buttons
  dom.btnGenOutline.addEventListener('click', () => {
    if (!state.currentStoryId) { showToast('请先选择故事'); return; }
    processUserMessage('帮我生成故事大纲');
  });

  dom.btnAddChar.addEventListener('click', showAddCharacterModal);
  dom.btnAddSetting.addEventListener('click', showAddSettingModal);
  dom.btnNewChapter.addEventListener('click', showNewChapterModal);

  // Panel item clicks (delegation for delete buttons and chapter items)
  dom.panelChars.addEventListener('click', handlePanelItemClick);
  dom.panelSettings.addEventListener('click', handlePanelItemClick);
  dom.panelChapters.addEventListener('click', handlePanelItemClick);

  // Keyboard shortcut: Ctrl+Enter as alternative
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
      e.preventDefault();
      sendMessage();
    }
  });
}

function handlePanelItemClick(e) {
  const btn = e.target.closest('[data-action]');
  if (!btn) return;

  let payload = {};
  try {
    payload = JSON.parse(btn.dataset.payload || '{}');
  } catch (_) {}

  const action = btn.dataset.action;
  handleAction(action, payload);
}

// ===================== Utility ===================== //
function escapeHtml(str) {
  if (typeof str !== 'string') return String(str || '');
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ===================== Init ===================== //
async function init() {
  initDomRefs();
  setupEventListeners();
  await loadStories();

  // Auto-select first story if exists
  if (state.stories.length > 0) {
    await selectStory(state.stories[0].id);
  }

  console.log('[Novel Agent] Frontend ready');
}

// Start when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
