// ===========================
// ALBATROSS AI — Newsletter Popup
// Uses FormSubmit.co — no backend needed
// Set YOUR_GMX_EMAIL below, then visit formsubmit.co to activate
// ===========================

const POPUP_EMAIL = 'albatrossai.online@gmail.com';
const POPUP_DELAY = 12000; // show after 12 seconds
const FORM_ACTION = `https://formsubmit.co/${POPUP_EMAIL}`;

// Don't show again this session
if (!sessionStorage.getItem('nlPopupShown')) {

  // Inject CSS
  const style = document.createElement('style');
  style.textContent = `
    #nl-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.75);
      z-index: 9999;
      align-items: center;
      justify-content: center;
      padding: 1rem;
    }
    #nl-overlay.open { display: flex; }
    #nl-box {
      background: #1a1a2e;
      border: 1px solid #00aaff;
      border-radius: 16px;
      padding: 2.5rem 2rem;
      max-width: 460px;
      width: 100%;
      text-align: center;
      position: relative;
      box-shadow: 0 0 40px rgba(0,170,255,0.2);
      font-family: 'Segoe UI', system-ui, sans-serif;
      color: #c8d6f0;
    }
    #nl-close {
      position: absolute;
      top: 1rem; right: 1.2rem;
      background: none; border: none;
      color: #c8d6f0; font-size: 1.4rem;
      cursor: pointer; opacity: 0.6;
    }
    #nl-close:hover { opacity: 1; }
    #nl-box .nl-icon { font-size: 2.5rem; margin-bottom: 0.75rem; }
    #nl-box h2 {
      font-size: 1.4rem;
      color: #f0f4ff;
      margin-bottom: 0.5rem;
    }
    #nl-box h2 span {
      background: linear-gradient(135deg, #00aaff, #7b2fff);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }
    #nl-box p {
      font-size: 0.9rem;
      opacity: 0.75;
      margin-bottom: 1.5rem;
      line-height: 1.6;
    }
    #nl-form { display: flex; flex-direction: column; gap: 0.75rem; }
    #nl-form input {
      padding: 0.75rem 1rem;
      background: #0d0d1a;
      border: 1px solid #2a2a4a;
      border-radius: 8px;
      color: #f0f4ff;
      font-size: 0.95rem;
      outline: none;
      transition: border-color 0.2s;
    }
    #nl-form input:focus { border-color: #00aaff; }
    #nl-form button {
      padding: 0.8rem;
      background: linear-gradient(135deg, #00aaff, #7b2fff);
      color: #fff;
      border: none;
      border-radius: 8px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: opacity 0.2s;
    }
    #nl-form button:hover { opacity: 0.85; }
    #nl-skip {
      margin-top: 0.75rem;
      font-size: 0.8rem;
      opacity: 0.5;
      cursor: pointer;
      background: none;
      border: none;
      color: #c8d6f0;
    }
    #nl-skip:hover { opacity: 0.8; }
    #nl-success {
      display: none;
      padding: 1rem 0;
    }
    #nl-success .nl-check { font-size: 2.5rem; margin-bottom: 0.5rem; }
    #nl-success p { opacity: 0.9; }
  `;
  document.head.appendChild(style);

  // Inject HTML
  const overlay = document.createElement('div');
  overlay.id = 'nl-overlay';
  overlay.innerHTML = `
    <div id="nl-box">
      <button id="nl-close" aria-label="Close">✕</button>
      <div class="nl-icon">🐦</div>
      <h2>Stay ahead of the <span>AI transition.</span></h2>
      <p>Free tools, automation tips, and build-in-public updates — straight to your inbox. No spam. Unsubscribe anytime.</p>
      <form id="nl-form" action="${FORM_ACTION}" method="POST">
        <input type="hidden" name="_subject" value="New Albatross AI Subscriber!">
        <input type="hidden" name="_captcha" value="false">
        <input type="hidden" name="_template" value="table">
        <input type="text" name="name" placeholder="Your name" required autocomplete="name">
        <input type="email" name="email" placeholder="Your email address" required autocomplete="email">
        <button type="submit">Get Free Updates →</button>
      </form>
      <div id="nl-success">
        <div class="nl-check">✅</div>
        <p>You're in. Welcome to the crew.</p>
      </div>
      <button id="nl-skip">No thanks, I'll figure it out myself</button>
    </div>
  `;
  document.body.appendChild(overlay);

  // Show/hide logic
  function showPopup() {
    overlay.classList.add('open');
    sessionStorage.setItem('nlPopupShown', '1');
  }
  function hidePopup() {
    overlay.classList.remove('open');
  }

  // Close button
  document.getElementById('nl-close').addEventListener('click', hidePopup);
  document.getElementById('nl-skip').addEventListener('click', hidePopup);

  // Close on outside click
  overlay.addEventListener('click', e => {
    if (e.target === overlay) hidePopup();
  });

  // Handle form submit
  document.getElementById('nl-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const data = new FormData(this);
    fetch(this.action, { method: 'POST', body: data, headers: { 'Accept': 'application/json' } })
      .then(() => {
        document.getElementById('nl-form').style.display = 'none';
        document.getElementById('nl-skip').style.display = 'none';
        document.getElementById('nl-success').style.display = 'block';
        setTimeout(hidePopup, 3000);
      })
      .catch(() => { this.submit(); }); // fallback to standard submit
  });

  // Exit intent (desktop)
  document.addEventListener('mouseleave', e => {
    if (e.clientY < 10) showPopup();
  });

  // Timed trigger (mobile fallback)
  setTimeout(showPopup, POPUP_DELAY);
}
