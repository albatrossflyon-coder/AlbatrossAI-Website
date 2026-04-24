# Albatross AI Website — Claude Project Instructions
# Last updated: 2026-03-23 | Agent: Ashes (Cowork)

## Brand Identity
- **Primary Colors:** Electric Blue (#00aaff), White (#f0f4ff), Dark Grey (#0d0d1a)
- **Gradient:** `linear-gradient(135deg, #00aaff, #7b2fff)`
- **Style:** Minimalist, futuristic, clean white-space. Cyberpunk AI aesthetic.
- **Logo:** `assets/images/Albatross AI logo.png`
- **Hero Image:** `assets/images/Thumbnail_Horizontal.png`
- **Main Video:** `assets/videos/Albatross_Main_Video.mp4`
- **Tagline:** *Devotion to the craft.*
- **Full brand voice:** `C:\Users\albat\Documents\Universal Brain Vault\Rules\Branding\brand_voice_guidelines.md`

## Project Structure
```
AlbatrossAI website/
├── .claude/CLAUDE.md          ← you are here
├── assets/
│   ├── images/                ← brand/hero images
│   ├── videos/                ← promo videos
│   └── icons/                 ← SVGs, favicon
├── css/style.css              ← single stylesheet, CSS vars defined here
├── js/main.js                 ← shared JS
├── index.html                 ← homepage
├── tools.html                 ← tools hub (links to all 4 tools)
├── ai-cost-estimator.html     ← Tool 1
├── resume-readiness-checker.html ← Tool 2
├── ai-roi-calculator.html     ← Tool 3
└── prompt-efficiency-scorer.html ← Tool 4
```

## Hosting
- **Provider:** GitHub Pages (via IONOS domain)
- **Domain:** albatrossai.online (NOT .com)
- **GitHub:** albatrossflyon-coder.github.io → master branch
- **Deploy:** push to master branch — auto-deploys via GitHub Pages

## Coding Rules
- Plain HTML, CSS, JS only — no frameworks
- Mobile-first responsive design
- Keep it clean and fast — no bloat, no unnecessary libraries
- All pages must link back to index.html and tools.html in nav
- CSS variables from style.css — never hardcode brand colors
- Tools are standalone HTML files — fully self-contained, no build step needed

## Content Rules (from brand voice guidelines)
- No filler openers ("Hey guys", "In this video", "Welcome back")
- Outcome-first hooks — lead with what the user gets
- Every sentence earns its place
- Phone-first readability — all text readable at mobile scale
