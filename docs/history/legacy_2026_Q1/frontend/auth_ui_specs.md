# 🎨 Frontend UI Specifications - Auth Service

This document defines the visual requirements for the authentication module of InternoCore. The design aims for a **Premium, High-Performance Industrial** aesthetic.

---

## 💎 Design System & Atmosphere
- **Core Aesthetic**: Dark mode by default, glassmorphism (frosted glass) effects on cards, and subtle micro-interactions.
- **Palette**:
    - **Primary**: Deep Industrial Blue (`#0A4F70`)
    - **Accent**: Cyber Green (`#32CD32`) for success/active states.
    - **Neutral**: Steel Gray (`#B0B7C0`) for typography and secondary elements.
- **Typography**: `Inter` for readability or `Outfit` for a more modern, geometric feel.

---

## 🖥️ View 1: Unified Login (Dual Mode)
The login screen must seamlessly handle both administrative users and plant floor operators.

### 🧩 Components
1. **Glassmorphism Container**: A central card with a blurred background.
2. **Tab Switcher (Optional/Subtle)**:
    - **Tab A: "Office/Admin"**: Conventional email/password fields.
    - **Tab B: "Plant Floor"**: Focused on scanning identity.
3. **Admin Form**:
    - "Email Address" input with icon.
    - "Password" input with "eye" icon to toggle visibility.
    - "Sign In" button with a hover gradient effect.
4. **RFID/Scan Overlay (The "Pulse" State)**:
    - A visual animation (rotating gear or pulsing hexagon) indicating the tablet is ready for a badge/RFID scan.
    - Text: *"Waiting for Badge Scan..."*
    - "Manual Login" link to slide back to the form.

---

## 🏢 View 2: Company Selection (The Handshake T1->T2)
Shown after a successful identity check if the user has >1 company.

### 🧩 Components
1. **Interactive Company Grid**: Cards representing each company the user can access.
    - Each card should show the Company Logo (or a styled initial).
    - Company Name and Role (e.g., "Owner", "Operator").
2. **Hover Effects**: Cards should scale slightly (1.02x) and glow with the Cyber Green accent when hovered.
3. **Search Bar**: A floating input to filter companies if the list is long.
4. **"Back to Login"**: Floating button to restart the session if errors occurred.

---

## ✨ Micro-Animations & States
- **Loading**: A precise engranage (gear) spinning in the center of the button or screen.
- **Error**: Input borders pulse in soft red; a "Shake" animation on the card for invalid credentials.
- **Success**: A Cyber Green "check" animation before transitioning to the dashboard.
- **Transitions**: Smooth "Slide-in" from the right when moving from Login to Company Selection.

---

## 📱 Responsiveness
- **Desktop**: Full background imagery (Industrial/Warehouse themes) with the card centered.
- **Tablet (Industrial)**: Large touch targets for the Company cards (minimum 48x48px).
- **Mobile**: Minimalist layout, focusing purely on the form or the Scan status.
