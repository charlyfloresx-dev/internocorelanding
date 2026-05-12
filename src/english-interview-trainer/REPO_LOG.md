# English Interview Trainer - Engineering Log

Tracking the stabilization, personalization, and technical evolution of the AI Interview Coach.

### 📌 Backlog / Próximos Pasos (V4/V5)
1. **TTS Premium:** Integrar voces de ElevenLabs para un realismo superior.
2. **Dashboard de Progreso:** Analítica histórica de la mejora en fluidez y vocabulario técnico.
3. **Mock Technical Interviews:** Simulacro de System Design en inglés.
4. **Hibridación Mobile (PWA/Capacitor):** Implementar `@angular/pwa` para instalación en pantalla de inicio. Evaluar migración a Capacitor para entrada en Google Play.
5. **Ergonomía Móvil V3:** Adaptar el wizard y los feedbacks a controles táctiles (Drawer-style modals) para una experiencia nativa.

---

## 2026-03-28: Phase 9 — Rebranding, Mobile Cleanup & Global Deployment
**Status:** ✅ Completed
**Focus:** InternoCore Identity, Multi-Platform PWA, Professional Audio Control.

### Technical Milestones
1. **Rebranding (InternoCore Identity):**
   - Migrated the entire application branding from *NexoSuite* to **InternoCore**.
   - Integrated the new **InternoCore SVG logo** into the V3 conversational header with responsive scaling.
2. **Mobile UI Cleanup (Distraction-Free UX):**
   - Removed the global navigation header (V1/V2/V3 tabs) to maximize screen real estate for mobile users (iPhone SE optimized).
   - Lifted the "Command Center" from the viewport bottom to avoid overlap with mobile gesture bars.
3. **Advanced Audio Playback Control:**
   - Implemented a reactive `isSpeaking` signal in `AudioService` for precise Text-to-Speech tracking.
   - Added a high-visibility, bouncing **"Stop AI Speaking"** button in the command center for instant audio interruption.
4. **CI/CD & Cloud Deployment:**
   - Initialized a dedicated [GitHub Repository](https://github.com/charlyfloresx-dev/EnglishInterviewTrainer.git).
   - Configured **Vercel** for automated builds and public PWA hosting.
   - Documented the **AWS S3 + CloudFront** low-cost deployment strategy for final production.

---

## 2026-03-28: Phase 8 — Conversational Automation & Live Mode (The ChatGPT Leap)
**Status:** ✅ Completed
**Focus:** Hands-Free UX, Persistence Architecture, Quota Resilience, Onboarding V3.

### Technical Milestones
1. **Hands-Free "Live Mode" (The VAD Leap):**
   - Implemented an automated turn-taking engine with **1.8s silence detection** (VAD - Voice Activity Detection simulation).
   - Orchestrated a **Bi-Directional Audio Chain**: AI-Speech-to-Mic (Automatically starts listening after the AI finishes speaking).
2. **Onboarding Wizard V3 (5-Step UX):**
   - Built a robust multi-step setup: **Google Auth** -> **BYOK Gemini Storage** -> **LinkedIn Link/CV Analysis** -> **Context Enrichment Questions** -> **Launch**.
   - Implemented state-aware persistence: Users can modify any previous step or auto-skip setup if done.
3. **Session & History Persistence:**
   - Designed a full JSON-based `localStorage` synchronization for `chatHistory` and User Profile.
   - Built a **"Resume Practice" logic** to survive page refreshes and browser crashes.
4. **Resilience & UI Logic:**
   - **Quota Guard**: Graceful catching of `429 (Resource Exhausted)` errors with auto-disable of Live Mode to prevent API lockout.
   - **Aggressive Regex Stripping**: Engineered a robust tag-cleaning system for `[COACHING]`, `[NATIVE RETRY]`, etc., to keep the main chat bubble 100% focused on dialogue.
   - **Collapsible Analytics (Insights Toggle)**: Redesigned the feedback panel as a toggleable accordion ("Ver Análisis") to optimize screen real estate.

---

## 2026-03-28: Phase 7 — Intelligent V3 (AI Job Interview & GC Authentication)
**Status:** ✅ Completed
**Focus:** OAuth2 Identity Injection, Generative AI Flow, Dynamic Audit Mode.

### Technical Milestones
1. **Google Identity Services (GIS):**
   - Implemented native `@google/accounts` script injection.
   - Built an autonomous Google Sign-In button supporting standard Flow and JWT decoding.
2. **Generative API Security (Bring Your Own Token):**
   - Integrated `REST API` calls to `Vertex AI` (`gen-lang-client-0828553044`) using the user's `Google Access Token`.
   - Prevented static API Key exhaustion. Designed basic SDK Fallback for dev environments.
3. **Prompt Architecture (Senior Technical Recruiter):**
   - Injected Context: *NexoSuite Senior Recruiter*.
   - Auditing Criteria: Tulip, QAD, SQL, Warehouse Automation (WIP).
   - Dynamically injected Candidate's Google Profile Name.
4. **V3 Conversational Interface:**
   - Implemented a continuous chat flow (`chatHistory`) replacing the static list of pre-defined questions.
   - Designed immersive Recruiter Bubbles with Audio Synthesis activation.
   - Migrated component to `OnPush` Change Detection for performance and established `V3` as the default application route.

---

## 2026-03-27: Phase 6 — Industrial Forensic Audit & Aerodynamic Navigation
**Status:** ✅ Completed
**Focus:** Visual Mimicry, High-Resolution Coaching, Ergonomic Navigation Control.

### Technical Milestones
1. **Aesthetic Parity (Mimicry Engine):**
   - Equalized typography between Master Script and User Response (`italic`, `font-medium`, `text-base`).
   - Implemented "Phonetic Brackets" in UI to reinforce the concept of voice auditing.
2. **Forensic Coaching (Hi-Res Audit):**
   - Increased coach sensitivity to **90%+ threshold** for professional seniority.
   - Added "Optimal Accuracy" status with emerald indicators for perfect scans.
3. **Aerodynamic Navigation (Red-Circle Relocation):**
   - Relocated the **Question Navigator** (Prev/Next/Progress) to the master script card's primary action zone.
   - Optimized UI layout to ensure 100% visibility of the feedback panel without scrolling.
4. **Technical Inventory Audit:**
   - Implemented a double-column "Found vs. Missing" terminology system for high-density analysis.

---

## 2026-03-28: Phase 5 — High-Density Ergonomics & Interface Purification
**Status:** ✅ Completed
**Focus:** UI Densification, Redundancy Elimination (Zero-Fat), Guided/Dashboard Ergonomics.

### Technical Milestones
1. **Guided Mode (V1) Nano-Scaling:**
   - Implemented a **High-Density Scaling System** (Nano headers, p-4 padding) to ensure 100% vertical visibility of Question + Master Script on any screen resolution.
   - Redesigned the navigation tabs as minimal icons to maximize content area.
2. **Dashboard V2 (Zero-Fat) Purification:**
   - **Data Consolidation**: Eliminated 100% of redundant transcriptions (Removed paragraph block vs. heatmap buttons).
   - **Interactive Heatmap Supremacy**: Unified all biometric feedback into a single, interactive word-button grid in the primary dashboard area.
3. **Ergonomic Control Integration:**
   - Relocated the **Master Record Button** to the "Bio-Heatmap" zone (Lower-Right) based on industrial ergonomics tests, unifying "Action" and "Result" in one eye-span.
4. **Compiler & Build Hardening:**
   - Stabilized standalone component architecture (Resolved TS-992012) and corrected Angular Core imports.
   - Forced bundle refreshment via "Touch" logic to ensure zero-stale builds.

---

## 2026-03-28: Phase 4 — Pro Dashboard & Forensic Audit
- **Dashboard V2 (All-in-One)**: Unified interface for questions, live-transcription, and immediate feedback on a single screen.
- **Forensic Audio Audit**: Implemented local audio playback and WEBM download for external diction analysis.
- **AI Pronunciation Tutor**: Context-aware phonetic coaching for industrial terms (Tulip, Class III, QAD, FDA).
- **Heuristic Normalization Engine**: Massive expansion of the phonetic dictionary (20+ technical mappings) to correct Speech API hallucinations.
- **Interactive Transcription**: Word-level playback and real-time visual heatmap.

---

## 2026-03-27: Phase 3 — Advanced Feedback & UI Hardening
**Status:** ✅ Completed
**Focus:** Vacancy-Aware Interviewing, Setup Workflow, Local Persistence.

### Technical Milestones
1. **Targeting Engine (JobService):**
   - Created `JobService` to persist long-form job descriptions in `localStorage`.
   - Implemented a baseline keyword extractor to match vacancy requirements with the internal question bank.
2. **Setup Workflow (SetupComponent):**
   - Designed a premium "Setup Mode" for pasting vacancies before the interview starts.
   - Integrated `isSetupMode` signal to drive the overall application flow.
3. **UX Navigation Hardening:**
   - Added an "Edit Target" navigation feature to allow seamless switching between different job vacancies without losing the session profile.

---

## 2026-03-26: Phase 1 — Audio Stabilization & Core Engine
**Status:** ✅ Completed
**Focus:** Windows/Realtek Hardware Fixes, Profile Injection, Interview Logic.

### Technical Milestones
1. **Hardware-Level Audio Stabilization (The "Silence Fix"):**
   - Resolved Windows/Realtek audio blocking by forcing `sampleRate: 48000Hz`.
   - Implemented a `GainNode` (x2.0) for digital amplification of low-input signal.
   - Configured `getUserMedia` in `RAW` mode to bypass OS-level noise filters that were muting the user's voice.
2. **Context-Aware Interview Engine:**
   - Bootstrapped `InterviewService` with a technical question bank (MES, Tulip, WIP reduction).
   - Injected User Profile (Senior MES Consultant) to tailor question difficulty and industry context.
3. **Core UX Implementation:**
   - Built the zoneless Angular 18 infrastructure with Tailwind CSS.
   - Integrated Web Speech API for real-time transcription and confidence scoring.

---

*(Log started on 2026-03-26 to document the stabilization of the proof-of-concept)*
