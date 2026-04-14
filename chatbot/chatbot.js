(function () {
  'use strict';

  var script = document.currentScript || (function () {
    var scripts = document.getElementsByTagName('script');
    return scripts[scripts.length - 1];
  })();

  var CLIENT_ID = script.getAttribute('data-client-id') || 'default';
  var API_BASE  = script.getAttribute('data-api') || 'https://albatrossai.online/api';
  var BOT_NAME  = script.getAttribute('data-name') || 'Builder Buddy';
  var BOT_COLOR = script.getAttribute('data-color') || '#00ff88';

  // --- Inject CSS ---
  var style = document.createElement('style');
  style.textContent = `
#aai-chat-root *{box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:0;padding:0}

/* Teaser card */
#aai-teaser{position:fixed;bottom:88px;right:20px;background:#161b22;border:1px solid rgba(255,255,255,0.12);border-radius:14px;padding:14px 16px;width:230px;z-index:9997;box-shadow:0 8px 24px rgba(0,0,0,0.5);animation:aai-slideup .4s ease}
#aai-teaser-close{position:absolute;top:7px;right:10px;background:none;border:none;color:#8b949e;cursor:pointer;font-size:13px;line-height:1}
#aai-teaser h4{font-size:13px;font-weight:700;color:#e6edf3;margin-bottom:5px}
#aai-teaser p{font-size:12px;color:#8b949e;line-height:1.45;margin-bottom:10px}
#aai-teaser ul{list-style:none;padding:0;margin-bottom:10px}
#aai-teaser ul li{font-size:11.5px;color:#8b949e;padding:2px 0}
#aai-teaser ul li::before{content:'✓ ';color:var(--aai-color,#00ff88)}
#aai-teaser-btn{width:100%;background:var(--aai-color,#00ff88);color:#000;border:none;border-radius:8px;padding:8px;font-size:12.5px;font-weight:700;cursor:pointer;transition:opacity .15s}
#aai-teaser-btn:hover{opacity:.9}
#aai-teaser.aai-hidden{display:none}
@keyframes aai-slideup{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}

/* Bubble */
#aai-chat-bubble{position:fixed;bottom:24px;right:24px;width:52px;height:52px;background:var(--aai-color,#00ff88);border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;z-index:9998;box-shadow:0 4px 16px rgba(0,255,136,0.35);transition:transform .2s,box-shadow .2s}
#aai-chat-bubble:hover{transform:scale(1.08)}
#aai-chat-bubble.aai-hidden{display:none}
#aai-chat-bubble svg{width:22px;height:22px;stroke:#000;fill:none;stroke-width:2}
#aai-bubble-label{position:fixed;bottom:30px;right:84px;background:#161b22;color:#e6edf3;font-size:12px;font-weight:600;padding:6px 11px;border-radius:20px;border:1px solid rgba(255,255,255,0.1);white-space:nowrap;z-index:9997;pointer-events:none;box-shadow:0 2px 8px rgba(0,0,0,0.4)}
#aai-bubble-label.aai-hidden{display:none}

/* Window */
#aai-chat-window{position:fixed;bottom:24px;right:24px;width:350px;max-height:530px;background:#0d1117;border:1px solid rgba(255,255,255,0.08);border-radius:16px;box-shadow:0 16px 48px rgba(0,0,0,0.6);display:flex;flex-direction:column;z-index:9999;opacity:0;transform:translateY(16px) scale(0.97);pointer-events:none;transition:opacity .2s ease,transform .2s ease;overflow:hidden}
#aai-chat-window.aai-open{opacity:1;transform:translateY(0) scale(1);pointer-events:all}

/* Header */
#aai-chat-header{display:flex;align-items:center;justify-content:space-between;padding:12px 14px;background:#161b22;border-bottom:1px solid rgba(255,255,255,0.08);flex-shrink:0}
#aai-chat-header-left{display:flex;align-items:center;gap:9px}
#aai-chat-avatar{width:34px;height:34px;background:var(--aai-color,#00ff88);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;color:#000;flex-shrink:0}
#aai-chat-name{font-size:13px;font-weight:600;color:#e6edf3}
#aai-chat-status{font-size:11px;color:var(--aai-color,#00ff88)}
#aai-header-actions{display:flex;align-items:center;gap:6px}
#aai-voice-toggle{background:none;border:1px solid rgba(255,255,255,0.12);border-radius:6px;color:#8b949e;cursor:pointer;font-size:15px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;transition:color .15s,border-color .15s}
#aai-voice-toggle.aai-on{color:var(--aai-color,#00ff88);border-color:var(--aai-color,#00ff88)}
#aai-chat-close{background:none;border:none;color:#8b949e;cursor:pointer;font-size:15px;padding:4px;line-height:1;transition:color .15s}
#aai-chat-close:hover{color:#e6edf3}

/* Messages */
#aai-chat-messages{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:8px;scroll-behavior:smooth}
#aai-chat-messages::-webkit-scrollbar{width:3px}
#aai-chat-messages::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.1);border-radius:2px}
.aai-msg{display:flex;max-width:88%}
.aai-msg.aai-user{align-self:flex-end}
.aai-msg.aai-bot{align-self:flex-start}
.aai-bubble{padding:9px 13px;border-radius:12px;font-size:13px;line-height:1.55;color:#e6edf3;word-break:break-word}
.aai-msg.aai-user .aai-bubble{background:var(--aai-color,#00ff88);color:#000;border-bottom-right-radius:3px;font-weight:500}
.aai-msg.aai-bot .aai-bubble{background:#161b22;border:1px solid rgba(255,255,255,0.08);border-bottom-left-radius:3px}
.aai-typing-indicator{display:flex;gap:4px;align-items:center;padding:10px 14px}
.aai-typing-indicator span{width:6px;height:6px;background:#8b949e;border-radius:50%;animation:aai-bounce 1.2s infinite}
.aai-typing-indicator span:nth-child(2){animation-delay:.2s}
.aai-typing-indicator span:nth-child(3){animation-delay:.4s}
@keyframes aai-bounce{0%,60%,100%{transform:translateY(0);opacity:.5}30%{transform:translateY(-5px);opacity:1}}

/* Lead form */
#aai-lead-form{padding:14px;display:flex;flex-direction:column;gap:8px;border-top:1px solid rgba(255,255,255,0.08);background:#161b22;flex-shrink:0}
#aai-lead-form p{font-size:12px;color:#8b949e;line-height:1.4}
#aai-lead-form input{background:#0d1117;border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:8px 11px;color:#e6edf3;font-size:13px;outline:none;transition:border-color .15s}
#aai-lead-form input:focus{border-color:var(--aai-color,#00ff88)}
#aai-lead-form input::placeholder{color:#8b949e}
#aai-lead-submit{background:var(--aai-color,#00ff88);color:#000;border:none;border-radius:8px;padding:9px;font-size:13px;font-weight:600;cursor:pointer;transition:opacity .15s}
#aai-lead-submit:hover{opacity:.9}
#aai-lead-submit:disabled{opacity:.5;cursor:default}
#aai-lead-confirm{font-size:12px;color:var(--aai-color,#00ff88);text-align:center;font-weight:500}

/* Input area */
#aai-chat-input-area{display:flex;align-items:center;gap:7px;padding:10px 12px;border-top:1px solid rgba(255,255,255,0.08);background:#161b22;flex-shrink:0}
#aai-chat-input{flex:1;background:#0d1117;border:1px solid rgba(255,255,255,0.1);border-radius:9px;padding:8px 11px;color:#e6edf3;font-size:13px;outline:none;transition:border-color .15s}
#aai-chat-input:focus{border-color:var(--aai-color,#00ff88)}
#aai-chat-input::placeholder{color:#8b949e}
#aai-chat-send{width:34px;height:34px;min-width:34px;background:var(--aai-color,#00ff88);border:none;border-radius:50%;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:opacity .15s,transform .15s}
#aai-chat-send:hover{opacity:.9;transform:scale(1.05)}
#aai-chat-send svg{width:15px;height:15px;fill:#000}
@media(max-width:420px){#aai-chat-window{bottom:0;right:0;width:100%;max-height:72vh;border-radius:16px 16px 0 0}#aai-chat-bubble{bottom:18px;right:18px}#aai-teaser{right:12px;bottom:82px;width:calc(100% - 24px)}#aai-bubble-label{display:none}}
  `;
  document.head.appendChild(style);
  document.documentElement.style.setProperty('--aai-color', BOT_COLOR);

  // --- Build HTML ---
  var html = `
<div id="aai-bubble-label">Ask Builder Buddy</div>

<div id="aai-teaser">
  <button id="aai-teaser-close">&#10005;</button>
  <h4>&#129302; Builder Buddy</h4>
  <p>Get instant answers about your project — free.</p>
  <ul>
    <li>Tile, roofing &amp; material estimates</li>
    <li>Permits, codes &amp; timelines</li>
    <li>Bid &amp; contract questions</li>
    <li>Cost ranges for any trade</li>
  </ul>
  <button id="aai-teaser-btn">Ask a Question &rarr;</button>
</div>

<div id="aai-chat-bubble" title="Builder Buddy — Ask anything">
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
  </svg>
</div>

<div id="aai-chat-window">
  <div id="aai-chat-header">
    <div id="aai-chat-header-left">
      <div id="aai-chat-avatar">AI</div>
      <div>
        <div id="aai-chat-name">${BOT_NAME}</div>
        <div id="aai-chat-status">&#9679; Online</div>
      </div>
    </div>
    <div id="aai-header-actions">
      <button id="aai-voice-toggle" title="Toggle voice">&#128264;</button>
      <button id="aai-chat-close">&#10005;</button>
    </div>
  </div>

  <div id="aai-chat-messages">
    <div class="aai-msg aai-bot">
      <div class="aai-bubble">Hey! I'm Builder Buddy — your construction assistant. Ask me anything about bids, permits, costs, or material estimates. What's your project about?</div>
    </div>
  </div>

  <div id="aai-lead-form" style="display:none">
    <p>You've used your 3 free questions. Drop your info and we'll follow up with a free estimate!</p>
    <input id="aai-lead-name" type="text" placeholder="Your name" />
    <input id="aai-lead-phone" type="tel" placeholder="Phone number" />
    <input id="aai-lead-project" type="text" placeholder="Project type (optional)" />
    <button id="aai-lead-submit">Get Free Estimate</button>
    <div id="aai-lead-confirm" style="display:none">Thanks! We'll be in touch shortly.</div>
  </div>

  <div id="aai-chat-input-area">
    <input id="aai-chat-input" type="text" placeholder="Ask a construction question..." maxlength="300" />
    <button id="aai-chat-send">
      <svg viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
    </button>
  </div>
</div>`;

  var container = document.createElement('div');
  container.id = 'aai-chat-root';
  container.innerHTML = html;
  document.body.appendChild(container);

  // --- Elements ---
  var bubble      = document.getElementById('aai-chat-bubble');
  var bubbleLabel = document.getElementById('aai-bubble-label');
  var teaser      = document.getElementById('aai-teaser');
  var teaserClose = document.getElementById('aai-teaser-close');
  var teaserBtn   = document.getElementById('aai-teaser-btn');
  var window_     = document.getElementById('aai-chat-window');
  var closeBtn    = document.getElementById('aai-chat-close');
  var messages    = document.getElementById('aai-chat-messages');
  var input       = document.getElementById('aai-chat-input');
  var sendBtn     = document.getElementById('aai-chat-send');
  var leadForm    = document.getElementById('aai-lead-form');
  var inputArea   = document.getElementById('aai-chat-input-area');
  var leadName    = document.getElementById('aai-lead-name');
  var leadPhone   = document.getElementById('aai-lead-phone');
  var leadProject = document.getElementById('aai-lead-project');
  var leadSubmit  = document.getElementById('aai-lead-submit');
  var leadConfirm = document.getElementById('aai-lead-confirm');
  var voiceBtn    = document.getElementById('aai-voice-toggle');

  var isOpen    = false;
  var isLoading = false;
  var voiceOn   = true; // voice on by default
  var history   = []; // conversation memory

  // --- Voice (browser Speech Synthesis) ---
  function speak(text) {
    if (!voiceOn || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    var clean = text.replace(/\*\*/g, '').replace(/[#*_`]/g, '');
    var utt = new SpeechSynthesisUtterance(clean);
    utt.rate = 1.05;
    utt.pitch = 1;
    // Pick a natural voice if available
    var voices = window.speechSynthesis.getVoices();
    var preferred = voices.find(function(v) {
      return /Google US English|Samantha|Alex|Karen/.test(v.name);
    });
    if (preferred) utt.voice = preferred;
    window.speechSynthesis.speak(utt);
  }

  voiceBtn.classList.add('aai-on');
  voiceBtn.addEventListener('click', function () {
    voiceOn = !voiceOn;
    voiceBtn.classList.toggle('aai-on', voiceOn);
    voiceBtn.title = voiceOn ? 'Mute voice' : 'Unmute voice';
    voiceBtn.textContent = voiceOn ? '🔊' : '🔇';
    if (!voiceOn) window.speechSynthesis && window.speechSynthesis.cancel();
  });

  // --- Teaser auto-show after 3s ---
  setTimeout(function () {
    if (!isOpen) teaser.classList.remove('aai-hidden');
  }, 3000);

  teaserClose.addEventListener('click', function (e) {
    e.stopPropagation();
    teaser.classList.add('aai-hidden');
  });

  teaserBtn.addEventListener('click', function () {
    teaser.classList.add('aai-hidden');
    openChat();
  });

  // --- Toggle ---
  function openChat() {
    isOpen = true;
    window_.classList.add('aai-open');
    bubble.classList.add('aai-hidden');
    bubbleLabel.classList.add('aai-hidden');
    teaser.classList.add('aai-hidden');
    setTimeout(function () { input.focus(); }, 200);
    // Greet with voice on first open
    speak('Hey! I\'m Builder Buddy, your construction assistant. Ask me anything about bids, permits, costs, or material estimates. What\'s your project about?');
  }

  function closeChat() {
    isOpen = false;
    window_.classList.remove('aai-open');
    bubble.classList.remove('aai-hidden');
    bubbleLabel.classList.remove('aai-hidden');
    window.speechSynthesis && window.speechSynthesis.cancel();
  }

  bubble.addEventListener('click', openChat);
  bubbleLabel.addEventListener('click', openChat);
  closeBtn.addEventListener('click', closeChat);

  // --- Send ---
  function sendMessage() {
    var text = input.value.trim();
    if (!text || isLoading) return;

    appendMessage(text, 'user');
    input.value = '';
    isLoading = true;
    showTyping();

    // Add user message to history before sending
    history.push({ role: 'user', text: text });

    fetch(API_BASE + '/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, client_id: CLIENT_ID, history: history.slice(0, -1) })
    })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      removeTyping();
      isLoading = false;

      if (data.blocked) {
        appendMessage(data.message, 'bot');
        speak(data.message);
        showLeadForm();
      } else if (data.answer) {
        appendMessage(data.answer, 'bot');
        speak(data.answer);
        // Add bot response to history
        history.push({ role: 'model', text: data.answer });
        if (data.queries_remaining === 1) {
          appendMessage('One free question remaining.', 'bot hint');
        }
      } else {
        appendMessage('Something went wrong. Please try again.', 'bot');
      }
    })
    .catch(function () {
      removeTyping();
      isLoading = false;
      // Remove the failed user message from history
      history.pop();
      appendMessage('Connection error. Please try again.', 'bot');
    });
  }

  sendBtn.addEventListener('click', sendMessage);
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') sendMessage();
  });

  // --- Lead form ---
  leadSubmit.addEventListener('click', function () {
    var name = leadName.value.trim();
    var phone = leadPhone.value.trim();
    if (!name || !phone) {
      leadName.style.border = name ? '' : '1px solid #ff4444';
      leadPhone.style.border = phone ? '' : '1px solid #ff4444';
      return;
    }
    leadSubmit.disabled = true;
    leadSubmit.textContent = 'Sending...';
    fetch(API_BASE + '/lead', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name, phone: phone, project: leadProject.value.trim(), client_id: CLIENT_ID })
    })
    .then(function (r) { return r.json(); })
    .then(function () {
      leadSubmit.style.display = 'none';
      leadConfirm.style.display = 'block';
      speak('Thanks! We\'ll be in touch shortly.');
    })
    .catch(function () {
      leadSubmit.disabled = false;
      leadSubmit.textContent = 'Get Free Estimate';
    });
  });

  // --- Helpers ---
  function appendMessage(text, type) {
    var div = document.createElement('div');
    div.className = 'aai-msg aai-' + (type === 'user' ? 'user' : 'bot');
    var bub = document.createElement('div');
    bub.className = 'aai-bubble';
    if (type === 'bot hint') bub.style.opacity = '0.55';
    if (type === 'user') {
      bub.textContent = text;
    } else {
      // Render URLs as clickable links
      var escaped = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
      var linked = escaped.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener" style="color:var(--aai-color,#00ff88);text-decoration:underline;">$1</a>');
      // Render **bold**
      linked = linked.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
      // Render bullet points
      linked = linked.replace(/^• /gm, '&#8226; ');
      linked = linked.replace(/\n/g, '<br>');
      bub.innerHTML = linked;
    }
    div.appendChild(bub);
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function showTyping() {
    var div = document.createElement('div');
    div.className = 'aai-msg aai-bot';
    div.id = 'aai-typing';
    div.innerHTML = '<div class="aai-bubble aai-typing-indicator"><span></span><span></span><span></span></div>';
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function removeTyping() {
    var t = document.getElementById('aai-typing');
    if (t) t.remove();
  }

  function showLeadForm() {
    inputArea.style.display = 'none';
    leadForm.style.display = 'flex';
  }

})();
