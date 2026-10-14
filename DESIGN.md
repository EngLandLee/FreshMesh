---
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 FreshMesh-DXOS contributors
name: FreshMesh-DXOS
description: Evidence-first process workspace for perishable-goods transfers
colors:
  primary: "#1d5141"
  primary-deep: "#102b25"
  paper: "#f6f8f3"
  surface: "#ffffff"
  ink: "#17342d"
  muted: "#5d7068"
  line: "#d6e0d8"
  mint: "#e6f1e8"
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
  sm: "7px"
  md: "12px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    padding: "8px 14px"
---

# Design System: FreshMesh-DXOS

## Overview

**Creative North Star: "Bàn điều phối có trách nhiệm"**

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

Desktop uses a sidebar and a task-oriented content pane. Narrow screens move
navigation into a horizontal strip and stack content. Tables may scroll within
their container; the document must not overflow horizontally at a 390px viewport.

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
