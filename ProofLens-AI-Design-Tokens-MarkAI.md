# ProofLens AI — Design Tokens & Motion System

**Final visual reference:** [MarkAI — AI for Marketing Web App (Chatting with AI)](https://dribbble.com/shots/26836296-MarkAI-AI-for-Marketing-Web-App-Chatting-with-AI)  
**Product:** ProofLens AI — evidence-first document intelligence platform.

> **Reference replacement:** This document supersedes the previous Dribbble reference. Do not use the previous “AI Chatbot Web App UI” link. Use only the MarkAI reference above as the primary Dribbble reference.

## 1. Design direction

The selected MarkAI page describes a clean AI chat interface, intuitive message flow, smart suggestions, and a minimal dashboard. Its described flow includes Dashboard, AI Prompt Builder, Results Viewer, History Log, and Settings.

Adapt the visual principles—not marketing-specific features—to ProofLens AI. ProofLens remains an evidence-first document intelligence workspace.

Preserve existing workflows where implemented:
- Document/PDF upload and library
- Evidence-based Q&A
- Page-level citations and source inspection
- Claim verification and conflicting evidence
- Explicit insufficient-evidence responses
- Cross-document comparison
- Existing account/workspace, history, and settings features

Keep answers readable, citations close to supported claims, and source inspection easy to access. Inspect the actual Dribbble screenshot before making exact pixel-level claims.

## 2. Color tokens

The retrieved page description does not provide a verified color palette. **Do not reuse the previous reference's palette by default.** Inspect the new MarkAI screenshot and the existing ProofLens UI, then define values that fit the new reference and maintain accessibility.

Use one centralized token source. This semantic structure is a template; replace the comments with verified and tested values after inspecting the screenshot.

```css
:root {
  /* Surfaces */
  --color-canvas: /* inspect reference and set */;
  --color-surface: /* inspect reference and set */;
  --color-surface-subtle: /* inspect reference and set */;
  --color-border: /* accessible border */;
  --color-border-strong: /* accessible strong border */;

  /* Text */
  --color-text-primary: /* high contrast */;
  --color-text-secondary: /* accessible secondary text */;
  --color-text-muted: /* readable muted text */;
  --color-text-inverse: /* text on strong surfaces */;

  /* Interaction */
  --color-brand: /* inspect reference and set */;
  --color-brand-hover: /* validate hover state */;
  --color-accent: /* inspect reference and set */;
  --color-accent-soft: /* subtle surface */;
  --color-link: /* accessible citation/link color */;
  --color-link-hover: /* validated hover color */;
  --color-focus-ring: /* clearly visible focus color */;

  /* Semantic states */
  --color-success: /* real success state */;
  --color-success-soft: /* subtle success surface */;
  --color-warning: /* real warning state */;
  --color-warning-soft: /* subtle warning surface */;
  --color-danger: /* error/destructive state */;
  --color-danger-soft: /* subtle danger surface */;
  --color-info: /* informational state */;
  --color-info-soft: /* subtle info surface */;
}
```

Rules:
- Use the brand color for important actions, not every element.
- Use accent colors sparingly.
- Citations must look interactive.
- Only show success/warning/danger for real states.
- Never label an AI answer “verified” unless actual verification logic supports it.
- Clearly communicate insufficient evidence; never style unsupported claims as confirmed.
- Validate relevant contrast against WCAG 2.2 AA where applicable (generally 4.5:1 for normal text and 3:1 for large text/meaningful graphics). Do not claim compliance without testing.

## 3. Typography tokens

Inspect the existing frontend first. Keep the current font if it is readable and suitable; do not add a font only for novelty. Avoid blurry typography, ultra-light weights, cramped line height, and low-contrast labels.

```css
:root {
  --font-sans: /* existing project font stack where possible */;
  --font-mono: /* existing monospace stack */;

  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-md: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;
  --text-4xl: 2.25rem;

  --line-tight: 1.2;
  --line-heading: 1.3;
  --line-body: 1.55;
  --line-relaxed: 1.7;

  --weight-regular: 400;
  --weight-medium: 500;
  --weight-semibold: 600;
  --weight-bold: 700;
}
```

Body text should normally be 14–16px; citation labels and metadata should generally be 12–14px and remain legible. Use monospace only for technical identifiers or code-like values. Keep answer text and source excerpts selectable.

## 4. Spacing, layout, radius, elevation

Reuse the existing project's spacing and breakpoint system if one exists. Avoid introducing competing systems.

```css
:root {
  --space-0: 0;
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
  --space-16: 4rem;

  --content-max: 1440px;
  --reading-max: 760px;
  --sidebar-width: 248px;
  --source-panel-width: 360px;
  --topbar-height: 64px;

  --radius-xs: 4px;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  --radius-pill: 999px;

  --shadow-xs: 0 1px 2px rgb(0 0 0 / 5%);
  --shadow-sm: 0 2px 8px rgb(0 0 0 / 6%);
  --shadow-md: 0 8px 24px rgb(0 0 0 / 9%);
  --shadow-dialog: 0 20px 60px rgb(0 0 0 / 18%);
}
```

Treat dimensions as starting points, not rigid requirements. Match the new reference where confirmed and preserve layouts that already work. Prefer subtle borders and clear surface hierarchy over excessive shadows, glassmorphism, or blur.

## 5. Component guidance

### Buttons and inputs
Use consistent primary, secondary, ghost, and destructive variants. Include hover, pressed, disabled, loading, and keyboard-focus states. Inputs need readable placeholders and visible focus/error states. Never clear user input just because a request failed.

### Chat and answers
Follow the reference's clear conversational flow where appropriate. Smart suggestions must map to supported actions or be clearly presented as suggestions. Differentiate user prompts from assistant answers with restrained visual cues. Keep long answers structured and readable; do not animate every word by default.

### Evidence and citations
- Make citation controls clearly interactive.
- Show document name and page number when available.
- Open the matching source/page when that feature exists.
- Distinguish supporting evidence, conflicting evidence, and insufficient evidence.
- Never fabricate citations, page numbers, quotations, confidence scores, or verification badges.
- Keep source excerpts visually distinct from AI-generated summaries.

### Documents, history, and settings
Apply the reference's organizational principles where appropriate, but do not copy marketing-specific features. Show accurate upload, processing, ready, and failed states. Drag-and-drop must not be the only upload method. Preserve existing history/settings behavior and do not mock successful ingestion or AI responses.

## 6. Motion tokens

```css
:root {
  --motion-instant: 100ms;
  --motion-fast: 160ms;
  --motion-normal: 220ms;
  --motion-slow: 320ms;
  --ease-standard: cubic-bezier(0.2, 0, 0, 1);
  --ease-emphasized: cubic-bezier(0.2, 0.8, 0.2, 1);
}
```

## 7. GSAP + ScrollTrigger, Framer Motion, and Lenis

Inspect installed dependencies first. Use these libraries only if already present or installation is explicitly approved. Do not create competing animation systems.

**GSAP + ScrollTrigger**
- Use for selected section entrances and meaningful scroll-triggered reveals.
- Avoid excessive per-element animations, scroll hijacking, or disruptive pinned sections.
- Clean up timelines and ScrollTrigger instances correctly.

**Framer Motion**
- Use for React component transitions such as dialogs, drawers, menus, popovers, and small layout/state changes.
- Prefer short opacity and subtle transform transitions.
- Do not animate the same element with GSAP and Framer Motion simultaneously.

**Lenis**
- Use for smooth scrolling only if compatible with the router, nested scroll areas, source/document panels, dialogs, anchors, and keyboard navigation.
- Do not create duplicate Lenis instances.
- Clean up animation loops and event listeners.
- Prefer native scrolling if smooth scrolling interferes with source navigation or accessibility.

Motion guidelines: hover/focus 100–160ms; small menus/panels 160–220ms; dialogs/drawers approximately 180–280ms; section reveals approximately 250–450ms only when useful. Prefer opacity and subtle transforms. Respect `prefers-reduced-motion`; disable nonessential parallax/reveals and preserve usable native/reduced scrolling.

## 8. Responsive behavior and accessibility

Use the project's current breakpoints if available. Verify:
- Keyboard navigation and visible focus
- Accessible names for icon-only controls
- Dialog/menu focus management
- Citation/source panel behavior on mobile
- Composer behavior with mobile keyboards
- Comparison views without horizontal overflow
- Screen-reader announcements for important asynchronous states
- Reduced-motion behavior and contrast

Do not rely on color alone to communicate evidence status. Do not claim accessibility compliance without testing.

## 9. Antigravity implementation requirements

1. Read `AGENTS.md` and this file.
2. Inspect the current repository and UI before editing.
3. Use only the MarkAI Dribbble link at the top as the primary reference. Remove the previous Dribbble link from active design instructions and implementation prompts.
4. Treat the existing repository as the source of truth. Do not rebuild from scratch.
5. Apply the smallest coherent set of changes needed to implement the new reference direction.
6. Create/update one centralized design-token source consistent with the current stack. Do not duplicate tokens or create competing sources of truth.
7. Inspect the actual new screenshot before finalizing exact colors, typography, and layout measurements. Do not reuse the old reference's palette unless independently confirmed in this reference or deliberately selected after visual review.
8. Adapt the design to ProofLens evidence workflows; do not add marketing-specific features.
9. Inspect installed dependencies before using GSAP, ScrollTrigger, Framer Motion, or Lenis. Do not install packages without approval.
10. Preserve existing routes, APIs, authentication, authorization, account/workspace isolation, ingestion, retrieval, citations, and backend behavior.
11. Never access, read, print, modify, or expose `.env` files or secret values. Never hardcode credentials.
12. Do not add fake AI answers, mock citations, fabricated evidence states, or pretend-success flows.
13. Do not change schemas, migrations, deployment, or backend logic for this visual task.
14. Test existing supported flows: upload, question submission, answer rendering, citation/source inspection, insufficient-evidence behavior, and responsive navigation.
15. Run available build, lint, and relevant tests; report only results actually observed.
16. Report changed files, interactions tested, actual test results, and remaining gaps.

## 10. Definition of done

- MarkAI is the sole primary Dribbble reference in this specification.
- The previous Dribbble reference has been removed from active instructions.
- The design is adapted to ProofLens, not copied as a marketing app.
- One centralized token system is applied consistently.
- Citations, source inspection, conflicting evidence, and insufficient-evidence states remain clear.
- Existing routes, backend functionality, authentication, and account/workspace isolation remain intact.
- Motion is purposeful, non-conflicting, responsive, and reduced-motion aware.
- No secrets are accessed or exposed; no unapproved dependencies or destructive changes are introduced.
- Available build, lint, and relevant tests are run, with real results reported.

## 11. Source-derived details versus adaptation

**Source-derived:** The MarkAI Dribbble page describes a clean AI chat interface, intuitive message flow, smart suggestions, and a minimal dashboard. It lists Dashboard, AI Prompt Builder, Results Viewer, History Log, and Settings in its described flow.

**ProofLens-specific adaptation:** Evidence-based answers, citations, page/source inspection, claim verification, insufficient-evidence states, accessibility requirements, and preservation of existing functionality are requirements for adapting the reference; they are not claims about MarkAI itself.

**Color limitation:** The retrieved page description does not provide a verified palette. Inspect the actual screenshot before locking final color values.
