---
name: Ortho-Cardio CRM
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#c2c6d4'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#8c909e'
  outline-variant: '#424752'
  surface-tint: '#acc7ff'
  primary: '#acc7ff'
  on-primary: '#002f67'
  primary-container: '#0056b3'
  on-primary-container: '#bbd0ff'
  inverse-primary: '#115cb9'
  secondary: '#b9c7e4'
  on-secondary: '#233148'
  secondary-container: '#3c4962'
  on-secondary-container: '#abb9d6'
  tertiary: '#ffb3b1'
  on-tertiary: '#680011'
  tertiary-container: '#b30b27'
  on-tertiary-container: '#ffc1bf'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d7e2ff'
  primary-fixed-dim: '#acc7ff'
  on-primary-fixed: '#001a40'
  on-primary-fixed-variant: '#004491'
  secondary-fixed: '#d6e3ff'
  secondary-fixed-dim: '#b9c7e4'
  on-secondary-fixed: '#0d1c32'
  on-secondary-fixed-variant: '#39475f'
  tertiary-fixed: '#ffdad8'
  tertiary-fixed-dim: '#ffb3b1'
  on-tertiary-fixed: '#410007'
  on-tertiary-fixed-variant: '#92001c'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  h1:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  h2:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  h3:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '500'
    lineHeight: '1.4'
    letterSpacing: '0'
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: 0.08em
  metadata:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.4'
    letterSpacing: '0'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
  gutter: 24px
  margin: 32px
---

## Brand & Style

The design system is engineered for high-stakes medical environments, prioritizing clinical precision and executive reliability. It targets surgeons, hospital administrators, and medical device representatives who require a clear, undistracted view of complex data.

The style is defined as **Corporate Minimalism**. It avoids decorative elements in favor of functional hierarchy. By removing borders and relying on tonal depth, the UI achieves a "fluid glass" feel that remains strictly professional. The emotional response is one of calm authority—a silent partner in the operating room or the boardroom that presents critical patient and inventory data without visual noise. There are no emojis, pastels, or whimsical interactions; every animation and transition is measured and purposeful.

## Colors

The color palette leverages deep, low-light values to reduce eye strain during long clinical shifts. 

- **Primary Canvas:** The foundational background uses `#121212`, while elevated surfaces (cards, panels) use `#1a1a1a`. 
- **The Navy Layer:** The deep navy blue (`#0a192f`) acts as a "semantic surface." It is used for persistent navigational elements like the sidebar or header to provide a subtle structural anchor.
- **Accents:** The corporate blue (`#0056b3`) is reserved for primary actions and active states. The red (`#e63946`) is used with extreme restraint, appearing only for critical alerts, cardiac status indicators, or urgent surgical requirements. 
- **Text:** To maintain high-end contrast, primary text is off-white (`#f8f9fa`), while metadata and inactive labels use a muted grey (`#adb5bd`).

## Typography

This design system utilizes **Inter** exclusively to ensure maximum legibility across various screen resolutions and lighting conditions. 

The typographic scale is highly structured. Headlines use a semi-bold weight with tight letter-spacing for a modern, high-end feel. Body text is optimized for readability with a generous 1.6 line height. A specific "Label Caps" style is implemented for sidebar headers and hospital metadata titles to create clear section breaks without the need for horizontal rules. In medical contexts, clarity is safety; therefore, no weight below 400 is permitted to ensure text never "breaks" on lower-quality medical monitors.

## Layout & Spacing

The layout philosophy is based on a **fixed 12-column grid** for main content areas, providing predictability for data-heavy dashboards. A persistent sidebar (width: 280px) sits on the left, using the deep navy surface.

We utilize an 8pt grid system (4px base unit) to maintain rhythmic consistency. 
- **Margins:** 32px global page margins to provide "breathing room" for a premium feel.
- **Gutters:** 24px fixed gutters between cards.
- **Density:** High density is allowed within data tables and medical charts, but global layout elements maintain generous padding (`lg` or `xl`) to prevent the software from feeling cluttered.

## Elevation & Depth

This design system completely eschews physical borders in favor of **Tonal Layers**. Hierarchy is established through background color shifts:
1. **Level 0 (Background):** `#121212` (The base).
2. **Level 1 (Cards/Containers):** `#1a1a1a` (Slightly lighter).
3. **Level 2 (Modals/Popovers):** `#242424` (Highest contrast).

To support this, we use **Ambient Shadows**. Shadows are not black; they are tinted with the primary navy (`#0a192f`) and have a very large blur radius (30px+) with low opacity (40%). This creates a "glow" effect that makes components feel as though they are floating in space rather than sitting on a flat surface.

## Shapes

The shape language is **Soft and Disciplined**. A uniform corner radius of `4px` (0.25rem) is applied to all standard containers, buttons, and input fields. This provides a modern touch while maintaining the "sharpness" expected in a medical/technological environment. Larger layout sections, like the main dashboard canvas, can utilize an `8px` radius to slightly soften the overall interface. Circular elements are reserved strictly for status indicators (e.g., connectivity, cardiac rhythm pulses).

## Components

### Toggle Switches
Professional toggles are minimalist. The track uses `#242424` when off and `#0056b3` when on. The "thumb" is a flat white circle with no shadow. No "X" or "Check" icons are used; the color shift provides the state change.

### Chat Bubbles
For professional communication between surgeons and reps:
- **Internal User:** Deep Navy (`#0a192f`) bubbles, right-aligned.
- **External/System:** Charcoal (`#1a1a1a`) bubbles, left-aligned.
Bubbles use a `4px` radius on all corners, with no tails, keeping the look clean and streamlined.

### Sidebar Items (Hospital Metadata)
Sidebar navigation items are grouped by Hospital. The Hospital name is displayed in "Label-Caps" typography. Beneath it, metadata (e.g., "OR Room 4", "Dr. Aris", "Live Inventory") is shown in a smaller, muted gray font. Hover states for sidebar items use a subtle background tint of the primary blue at 10% opacity, rather than a border.

### Buttons
Primary buttons are solid `#0056b3` with white text. Secondary buttons have no background but use a ghost-style blue text. There are no outlined buttons in the design system; interaction is signified by depth and color intensity.

### Input Fields
Inputs are borderless. They utilize a slightly darker background than the surface they sit on (`#121212` on a `#1a1a1a` card) to create a "recessed" feel. The focus state is indicated by a 2px blue underline.