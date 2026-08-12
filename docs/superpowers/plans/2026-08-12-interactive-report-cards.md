# Interactive Report Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Glasshouse cards feel tactile on hover and open into an accessible full-page reading view with richer local detail.

**Architecture:** Metrics attach deterministic detail text to every card. The renderer emits progressively enhanced semantic cards, one reusable native dialog, inline CSS motion, and a small inline controller for modal state, navigation, hashes, and focus.

**Tech Stack:** Python 3.11, HTML/CSS/SVG, vanilla JavaScript, `unittest`, `uv`.

## Global Constraints

- No external assets, libraries, model calls, or network calls.
- The card grid remains readable when JavaScript is unavailable.
- Motion respects `prefers-reduced-motion` and does not loop.
- Modal behavior is keyboard accessible and removed from print.

### Task 1: Deterministic card details

**Files:** Modify `glasshouse/metrics.py` and `tests/test_glasshouse.py`.

- [ ] Write failing tests that every card has meaningful `detail` text and that sensitive card values still pass through the existing recursive scrubber.
- [ ] Add card-specific explanatory detail using aggregate inputs only.
- [ ] Run focused and full tests.

### Task 2: Interactive renderer

**Files:** Modify `glasshouse/render.py` and `tests/test_glasshouse.py`.

- [ ] Write failing renderer tests for semantic activation, dialog structure, escaped detail, hover wiggle, reduced motion, close/navigation controls, URL hashes, and focus restoration.
- [ ] Implement the reusable expanded-card dialog, inline controller, and refined interaction styling.
- [ ] Run all tests and regenerate the real report.
- [ ] Inspect desktop, expanded, keyboard, and mobile states in the browser; correct verified issues.
- [ ] Build the wheel, validate the skill, and commit.
