---
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
name: FreshMesh-DXOS
description: Evidence-first process workspace for perishable-goods transfers
colors:
  primary: "#215b43"
  primary-deep: "#112f26"
  paper: "#f5f6f2"
  surface: "#ffffff"
  ink: "#213e30"
  muted: "#617064"
  line: "#dfe5dc"
  mint: "#edf3e8"
  danger: "#a53c3a"
typography:
  body:
    fontFamily: '"IBM Plex Sans", "Segoe UI", ui-sans-serif, system-ui, sans-serif'
    fontSize: "14px"
    lineHeight: 1.5
  label:
    fontSize: "12px"
    fontWeight: 700
rounded:
  sm: "8px"
  md: "14px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    padding: "9px 15px"
---

# Design System: FreshMesh-DXOS

## Overview

**Creative North Star: "Nhịp hàng tươi, trong một tầm nhìn"**

This records the implemented operational interface, not an additional user-approved
brand claim. People scan stock, approve proposals and record actual handovers;
status and accountability lead, decoration does not. Vietnamese copy explains
errors, assumptions and next actions.

## Colors

Forest tones identify actions and active navigation. Paper and white surfaces
separate the workspace from tables and evidence. Muted text remains readable;
red is reserved for failure/rejection, not a decorative accent.

## Typography

The declared body stack uses locally available fonts and system fallbacks; no IBM
Plex font asset is bundled or claimed to be installed. Body text and label sizes
are defined above. Monospace is reserved for transfer identifiers, not general prose.

## Layout

Desktop uses a deep forest sidebar, a white identity bar, and a bright operational
canvas. A compact six-state strip establishes the transfer pipeline; the scoped
store network is visible before the full-width inventory table. Long received-lot
identifiers use compact visible text with full identifiers available in their title.
At 1000px the map and itinerary stack; at 720px navigation becomes a horizontal
strip. Tables scroll inside their container. The document must not overflow at
390px. Projection readability and task hierarchy determine spacing and contrast.

## Elevation & Depth

Surfaces use restrained borders and tonal contrast. Dialogs protect focused,
consequential actions. Toasts convey feedback without intercepting pointer input.

## Shapes

Small controls and larger sections use the two radius tokens above. Status tags
use compact rounded shapes and retain an explicit text label.

## Components

Primary/secondary buttons, labelled fields, active navigation and status tags are
extracted from `portal/styles.css`; corresponding preview snippets are in
`.impeccable/design.json`. Every action needs pending, error and access-denied
behavior. Role hiding is not authorization: the server enforces policy.

## Do's and Don'ts

- Do keep task status, actor, actual quantity and evidence visible.
- Do honor `[hidden]` and reduced-motion preferences.
- Do expose data provenance and estimated-route limitations.
- Don't cover active controls with toast overlays.
- Don't fabricate business metrics, customers or AI confidence.
- Don't replace the operational interface with marketing decoration.

## Offline route simulation

The authored SVG uses pale city blocks, white schematic roads, green open areas,
and a blue waterway. These contextual shapes are explicitly illustrative and do
not claim geographic accuracy. Valid authorized store coordinates are projected
proportionally with longitude correction; real route stop order is kept from the
API. A source is added only when visible transfers identify one source and that
store has valid coordinates. Without that evidence, destinations are labelled as
destinations and the missing origin is disclosed.

The default presentation route has four explicitly fictitious points. It lives
only in browser memory and never creates, dispatches, delivers, or receives a
backend record. A selector separates it from saved routes. Play, pause, reset,
speed, stop selection, and zoom are local presentation controls. Progress measures
the simulation timeline, not a real delivery or ETA. Leaving the route view or
hiding the browser tab pauses playback. Reduced-motion users get discrete stop
positions instead of continuous vehicle movement.

## Iconography and browser details

Navigation, the brand mark, stores, and map controls use authored SVG linework at
a consistent stroke weight. Native controls retain labelled focus states; selected
map stops have both visual and ARIA state. Selection, caret, scrollbars and tabular
numerals use the same palette. Background contrast and restrained borders supply
depth; dialogs and floating map controls are the only elevated surfaces.

Functional interface text has an 11px floor; main controls and inventory labels use
12–14px. SVG diagram labels scale within the map; full stop names remain available
in the HTML itinerary and store list at functional text sizes.
