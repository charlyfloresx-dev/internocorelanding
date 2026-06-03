# InternoCore Landing Page
## v2.0 (Dark Industrial SaaS) → v2.1 (Pain-First, A/B Testing)

**Status:** 🔴 v2.0 Live on Vercel | 🟡 v2.1 In Development  
**Last Updated:** 2026-06-04  
**Owner:** Carlos Flores

---

## 📍 QUICK START

### Running Locally
```bash
cd src/landing

# Option 1: Live server (recommended)
npm run dev

# Option 2: Python HTTP server
npm run start

# Browser: http://localhost:3100
```

### Deploying to Vercel
```bash
npm i -g vercel
vercel

# Follow prompts:
# Project name: internocore-landing
# Build command: (leave blank)
# Publish directory: ./
```

**Current URL:** [https://internocore-landing.vercel.app](https://internocore-landing.vercel.app)

---

## 🏗️ ARCHITECTURE

```
src/landing/
├── index.html              # Main page (hero + modules + pricing)
├── plans.html              # Pricing details + comparison table
├── ticket-access.html      # Tickets module demo
├── style.css               # Dark theme (cyan #00e5ff accent)
├── app.js                  # Vanilla JS (i18n, animations, counter)
├── locales/
│   ├── es.json            # Spanish translations
│   └── en.json            # English translations
├── package.json            # Dependencies (minimal: motion via CDN)
└── README.md              # This file
```

### Tech Stack
- **Frontend:** Vanilla HTML/CSS/JS (no build step)
- **Styling:** CSS variables + custom dark theme
- **Animations:** Framer Motion (vanilla-JS via CDN)
- **i18n:** Manual JSON switching (ES/EN)
- **Hosting:** Vercel (free, auto-deploy from git)

---

## 📊 CURRENT SCORECARD (v2.0)

| Aspect | Score | Status |
|--------|-------|--------|
| Design & UX | 9/10 | ✅ Beautiful, responsive, professional |
| Architect Credibility | 9/10 | ✅ Safran, DJO, Outset credentials visible |
| Module Clarity | 7/10 | ⚠️ Features listed but no results tied |
| Value Proposition | 5/10 | 🔴 **CRITICAL:** "MES = control" but why? |
| Social Proof | 3/10 | 🔴 **CRITICAL:** No customer testimonials |
| CTA Quality | 6/10 | 🔴 Generic "Demo" + "Select Plan" buttons |
| Copy Resonance | 4/10 | 🔴 **CRITICAL:** Tech jargon (CQRS, RLS) ≠ director speak |
| Urgency/FOMO | 2/10 | 🔴 No deadline, no scarcity, no incentive |
| **TOTAL** | **52/100** | ⚠️ Looks good, doesn't convert |

---

## 🎯 v2.1 ROADMAP (Next 2 Weeks)

### TIER 1: Copy Rewrite (Do First — No Dev)
```
□ Hero: "De la Planta..." → "Paros de Línea: SOLUCIONADO en 90 Días"
□ Feature descriptions: Add metrics (8/month → 1/month, $4.8M → $40K)
□ Pricing: Emphasize payback (most plants ROI in 60 days)
□ Add case study banner (Safran WIP reduction with stats)
```

**Files to Update:**
- `es.json`: rewrite `hero.title`, `features.*_desc`, `pricing.*_list`
- `index.html`: add new section for case study between features + security

### TIER 2: Structure Changes (20 min CSS)
```
□ Add "Case Study" section (logo + snippet + video link)
□ Add "Trust Bar" (# plants, # pieces tracked, $ saved)
□ Add "Free Tools" section (2 calculators: ROI + Capacity)
□ Update CTA buttons (ladder: Demo → ROI Calc → Book Call)
```

### TIER 3: A/B Testing Setup
```
□ Landing v2.1a: Pain-first (paros/loss aversion)
□ Landing v2.1b: Efficiency-first (hidden capacity)
□ Landing v2.1c: Compliance-first (FDA/audit risk)
□ Split traffic 33/33/33 for 2 weeks
□ Winner becomes default, others archived
```

---

## 🎬 CONTENT NEEDED FOR v2.1

### 1. Case Study (Required for Week 1)
**Safran Aerospace — WIP Reduction**
```
Company: Safran Aerospace
Problem: WIP $4.8M blocked in ensamble
Solution: InternoCore MES + BOM explosion
Result: WIP → $40K in 60 days (99.2% reduction)
ROI: Payback in 45 days

Video: 2-min case study clip (if available)
PDF: 1-page downloadable summary
```

**File:** `docs/case_studies/safran_wip_reduction.md` (create)

### 2. Demo Video (Required for Week 1)
**BOM Explosion Feature (2 min)**
```
Scene 1 (0:00-0:30): Problem — Order lands, material missing
Scene 2 (0:30-1:00): Solution — MES predicts + alerts supply
Scene 3 (1:00-1:30): Results — Paros drop 8/month → 1/month
Scene 4 (1:30-2:00): CTA — Book call or watch again

Host: YouTube (unlisted)
Embed: YouTube iframe in landing + email pitch
```

**Status:** 🔴 Not recorded yet (Carlos to record this week)

### 3. Free Tools (Required for Week 2)
**MES ROI Calculator**
```
Inputs:
- # of production lines
- Paros/month (average)
- $/hour cost (production line downtime)

Output:
- $/month lost (current)
- $/month saved (if paros -87%)
- Payback time (months)

CTA: "Email me the full report" → lead capture
```

**WMS Capacity Planner**
```
Inputs:
- Current SKUs in inventory
- Growth projection (%)
- Rack type (pallets/bins)

Output:
- When warehouse fills (date)
- Cost of expansion (estimate)
- Savings from Density Guard (estimate)

CTA: "Reserve a 15-min consultation" → calendly
```

**Status:** 🔴 Not built yet (need simple HTML forms + Google Sheets backend)

---

## 📈 METRICS TO TRACK (Post-Launch)

### Landing Analytics (GA4)
```
Primary:
- Sessions/day
- Bounce rate by section
- Scroll depth (% reaching pricing)
- CTA click rate (Demo vs ROI Calc vs Book Call)
- Form conversions (email capture rate)

Segments:
- Traffic source (LinkedIn, email, direct)
- Device type (desktop vs mobile)
- Language (ES vs EN)

Targets (After v2.1 Launch):
- CTA CTR: >5% (current ~1% = bad)
- Form conversion: >3% (new)
- Pricing page reach: >40% (current ~35%)
```

### A/B Test Tracking
```
Week 1-2:
- v2.1a (Pain): open rate, CTR, conversions
- v2.1b (Efficiency): open rate, CTR, conversions
- v2.1c (Compliance): open rate, CTR, conversions

Winner = highest CTR + form submissions
```

---

## 🛠️ DEVELOPMENT CHECKLIST

### v2.1 Copy Rewrite (Today → Tomorrow)
- [ ] Read ANALISIS_LANDING_ACTUAL_VS_RECOMENDADO.md
- [ ] Copy pain-first hero examples to `es.json`
- [ ] Update feature descriptions with metrics
- [ ] Test i18n reload (refresh browser)
- [ ] Compare before/after side-by-side

### v2.1 Case Study Section (Day 2)
- [ ] Add `<section id="case-study">` to `index.html`
- [ ] Add CSS in `style.css` (mirror `.features` styling)
- [ ] Add case study HTML + Safran logo
- [ ] Add video embed (YouTube iframe)
- [ ] Test on mobile (responsive check)

### v2.1 Free Tools Section (Day 3)
- [ ] Create simple form HTML (inputs + calculate button)
- [ ] Add Google Sheets API call (or email form capture)
- [ ] Style to match landing theme
- [ ] Test form submission
- [ ] Add to landing before pricing section

### v2.1 Deploy (Day 4)
```bash
git add .
git commit -m "feat(landing): v2.1 pain-first copy + case study + CTAs"
git push
# Vercel auto-deploys
```

### v2.1 A/B Test Setup (Week 2)
- [ ] Create landing-v2.1a.html (pain variant)
- [ ] Create landing-v2.1b.html (efficiency variant)
- [ ] Create landing-v2.1c.html (compliance variant)
- [ ] Deploy to Vercel (3 URLs)
- [ ] Setup GA4 split test routing
- [ ] Monitor metrics daily

---

## 🚀 GO-TO-MARKET INTEGRATION

**Landing is Part of Larger GTM Strategy:**

```
Landing (v2.0 → v2.1) 
  ↓
Champion Hunt (10 prospects identified)
  ↓
Cold Email Campaign (200+ prospects, 3 variants)
  ↓
Free Tools (2 calculators drive email capture)
  ↓
Case Study (1 champion + results = social proof)
  ↓
Paid Customers (3-5 by Week 7)
```

**See Also:**
- `docs/ESTRATEGIA_GTM_FASE1_20260604.md` — Full strategy
- `docs/ANALISIS_LANDING_ACTUAL_VS_RECOMENDADO.md` — Detailed audit
- `docs/PITCH_TEMPLATE_CHAMPION_HUNT.md` — Sales templates

---

## 📝 TROUBLESHOOTING

### Landing not loading locally
```
Error: Cannot find module 'motion'?
Fix: motion is loaded via CDN, not npm. Check internet connection.
     If offline, comment out <script src="motion@latest..."></script>
```

### i18n not switching (ES ↔ EN)
```
Error: Text not updating when clicking language button?
Fix: 1. Check browser console for errors
     2. Verify es.json and en.json are valid JSON (no trailing commas)
     3. Clear browser cache (Ctrl+Shift+Delete)
     4. Refresh page
```

### Vercel deployment failed
```
Error: "npm run build failed"?
Fix: This landing has NO build step. If Vercel asks for build command,
     leave it blank. Select "public" as publish directory.
```

---

## 📞 CONTACT

**Landing Owner:** Carlos Flores  
**Questions/Issues:** Create GitHub issue or email `flores.montoya.carlos@gmail.com`

---

**Last Deployed:** 2026-06-04 (v2.0)  
**Next Release:** 2026-06-06 (v2.1 expected)  
**A/B Test Window:** 2026-06-10 → 2026-06-24 (14 days)
