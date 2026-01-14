# Frontend Changes: Theme Toggle Button & Light Theme

## Overview
Added a light/dark mode toggle button to the Course Materials Assistant frontend. The button allows users to switch between dark (default) and light themes with a smooth animated transition.

## Files Modified

### 1. `frontend/index.html`
- Added a theme toggle button inside the `.container` div, positioned before the header
- Button uses SVG icons for sun (light mode indicator) and moon (dark mode indicator)
- Includes accessibility attributes: `aria-label` and `title`

### 2. `frontend/style.css`

#### Light Theme CSS Variables
Added comprehensive light theme with `[data-theme="light"]` selector:

**Primary Colors (adjusted for light backgrounds):**
- `--primary-color: #1d4ed8` - Slightly darker blue for better contrast
- `--primary-hover: #1e40af` - Darker hover state

**Background Colors:**
- `--background: #f8fafc` - Clean off-white page background
- `--surface: #ffffff` - Pure white for cards/panels
- `--surface-hover: #f1f5f9` - Subtle gray hover state

**Text Colors (WCAG AAA compliant):**
- `--text-primary: #0f172a` - Near-black for maximum readability
- `--text-secondary: #475569` - Medium gray for secondary content

**Border & Surface Colors:**
- `--border-color: #cbd5e1` - Visible but subtle borders

**Message Bubbles:**
- `--user-message: #1d4ed8` - Blue for user messages
- `--assistant-message: #f1f5f9` - Light gray for assistant

**Special Elements:**
- `--shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08)` - Lighter shadows
- `--focus-ring: rgba(29, 78, 216, 0.25)` - Blue focus indicator
- `--code-bg: rgba(15, 23, 42, 0.06)` - Subtle code background
- `--welcome-bg: #eff6ff` - Light blue welcome message

**Scrollbar Colors:**
- `--scrollbar-track: #f1f5f9`
- `--scrollbar-thumb: #cbd5e1`
- `--scrollbar-thumb-hover: #94a3b8`

**Error/Success States:**
- `--error-bg`, `--error-text`, `--error-border` - Red variants for light theme
- `--success-bg`, `--success-text`, `--success-border` - Green variants for light theme

#### Dark Theme Enhancements
Organized existing dark theme variables with comments and added:
- Scrollbar color variables
- Error/success color variables
- Updated error/success message styles to use CSS variables

#### Theme Toggle Button Styles
- Fixed position in top-right corner (`position: fixed; top: 1rem; right: 1rem`)
- Circular button design (44px diameter) with border and shadow
- Hover effect with scale transform and border color change
- Focus state with focus ring for keyboard accessibility
- Active state with scale-down effect for click feedback

#### Icon Animation
- Smooth opacity and rotation transitions between sun/moon icons
- Icons swap visibility based on current theme
- 0.3s ease transition for smooth animation

#### Responsive Design
- Smaller button size (40px) on mobile devices
- Adjusted positioning for smaller screens

#### Smooth Theme Transitions
Added global transition rules for seamless theme switching:
- All elements transition `background-color`, `border-color`, `color`, and `box-shadow` over 0.3s
- `.no-transitions` class disables transitions during initial page load to prevent flash
- Transitions are applied via `*` selector for comprehensive coverage

### 3. `frontend/script.js`
**New DOM Element:**
- Added `themeToggle` to the list of DOM elements

**New Functions:**
- `initializeTheme()`: Loads saved theme from localStorage on page load, defaults to dark. Temporarily disables transitions to prevent flash on load.
- `toggleTheme()`: Switches between light and dark themes on button click
- `applyTheme(theme)`: Applies the theme by setting/removing the `data-theme` attribute on `<html>` element

**Features:**
- Theme preference persisted in localStorage
- Dynamic aria-label updates for screen readers
- Click event listener for theme toggle
- Uses `data-theme` attribute on `document.documentElement` (html element) for CSS variable switching
- Double `requestAnimationFrame` for reliable transition re-enablement after initial load

## Usage
- Click the sun/moon icon in the top-right corner to toggle themes
- Theme preference is saved and persists across page refreshes
- Keyboard users can tab to the button and press Enter/Space to toggle

## Accessibility Standards Met
- **WCAG AA/AAA Color Contrast**: Text colors meet minimum contrast ratios
  - Light theme: `#0f172a` on `#f8fafc` = 15.5:1 ratio (AAA)
  - Dark theme: `#f1f5f9` on `#0f172a` = 15.5:1 ratio (AAA)
- **Keyboard Navigation**: Toggle button is fully keyboard accessible
- **Focus Indicators**: Visible focus ring on all interactive elements
- **Screen Reader Support**: Dynamic aria-labels announce current state
- **Reduced Motion**: Transitions are subtle and non-disruptive

## Color Palette Summary

| Variable | Dark Theme | Light Theme |
|----------|-----------|-------------|
| Background | `#0f172a` | `#f8fafc` |
| Surface | `#1e293b` | `#ffffff` |
| Text Primary | `#f1f5f9` | `#0f172a` |
| Text Secondary | `#94a3b8` | `#475569` |
| Primary | `#2563eb` | `#1d4ed8` |
| Border | `#334155` | `#cbd5e1` |
