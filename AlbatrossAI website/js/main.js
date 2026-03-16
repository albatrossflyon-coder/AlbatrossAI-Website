// ===========================
// ALBATROSS AI — MAIN JS
// ===========================

// Mobile nav toggle
const hamburger = document.querySelector('.hamburger');
const navLinks = document.querySelector('.nav-links');

hamburger?.addEventListener('click', () => {
  navLinks.classList.toggle('open');
});

// Close nav on link click (mobile)
navLinks?.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => navLinks.classList.remove('open'));
});

// Contact form handler
const form = document.querySelector('.contact-form');
form?.addEventListener('submit', (e) => {
  e.preventDefault();
  const btn = form.querySelector('button[type="submit"]');
  btn.textContent = 'Message Sent!';
  btn.style.background = '#00cc77';
  form.reset();
  setTimeout(() => {
    btn.textContent = 'Send Message';
    btn.style.background = '';
  }, 3000);
});

// Doors modal
const doorsOverlay  = document.getElementById('doorsOverlay');
const doorsClose    = document.getElementById('doorsClose');
const contactTrigger = document.querySelector('.contact-trigger');

function openDoors()  { doorsOverlay.classList.add('open'); }
function closeDoors() { doorsOverlay.classList.remove('open'); }

contactTrigger?.addEventListener('click', openDoors);
doorsClose?.addEventListener('click', closeDoors);

// Also trigger from nav "Contact" link
document.querySelectorAll('a[href="#contact"]').forEach(a => {
  a.addEventListener('click', (e) => {
    e.preventDefault();
    openDoors();
  });
});

// Click outside to close
doorsOverlay?.addEventListener('click', (e) => {
  if (e.target === doorsOverlay) closeDoors();
});

// Email copy to clipboard
const emailBtn = document.querySelector('.door-email-btn');
emailBtn?.addEventListener('click', () => {
  const email = emailBtn.dataset.email;
  navigator.clipboard.writeText(email).then(() => {
    const label = emailBtn.querySelector('.email-label');
    label.textContent = 'Copied!';
    emailBtn.style.color = '#00ff99';
    setTimeout(() => {
      label.textContent = 'Email';
      emailBtn.style.color = '';
    }, 2000);
  });
});

// Wallpaper crossfade slideshow
const slide1 = document.querySelector('.wp-slide-1');
const slide2 = document.querySelector('.wp-slide-2');
if (slide1 && slide2) {
  let showing1 = true;
  setInterval(() => {
    showing1 = !showing1;
    slide1.style.opacity = showing1 ? '1' : '0';
    slide2.style.opacity = showing1 ? '0' : '1';
  }, 5000);
}

// Scroll fade-in animation
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.card, .service-item, .gallery-grid img').forEach(el => {
  el.classList.add('fade-in');
  observer.observe(el);
});
