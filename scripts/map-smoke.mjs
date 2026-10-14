// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 FreshMesh-DXOS contributors
// Read-only browser acceptance for the simulated map. No transfer or stock mutation.
import assert from 'node:assert/strict';
import { mkdir } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { chromium, expect } from '@playwright/test';

const base = (process.env.PORTAL_URL || 'http://localhost:3180').replace(/\/$/, '');
const shots = resolve(process.env.SCREENSHOT_DIR || 'dist/ui-redesign');
await mkdir(shots, { recursive: true });
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
page.setDefaultTimeout(20000);
const errors = [];
const writes = [];
page.on('pageerror', error => errors.push(error.message));
page.on('request', request => {
  if (new URL(request.url()).pathname.startsWith('/api/') &&
      !['GET', 'HEAD', 'OPTIONS'].includes(request.method())) {
    writes.push(`${request.method()} ${new URL(request.url()).pathname}`);
  }
});

const progress = () => page.locator('#map-progress').evaluate(el =>
  Number(el.value ?? el.getAttribute('aria-valuenow')));
const mapBox = () => page.locator('#route-map').evaluate(el =>
  (el.matches('svg') ? el : el.querySelector('svg')).getAttribute('viewBox'));
const noOverflow = () => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth);

try {
  await page.goto(base);
  await page.locator('#login-button').click();
  await page.locator('#username').fill(process.env.DEMO_OWNER || 'owner_a');
  await page.locator('#password').fill(process.env.DEMO_PASSWORD || 'demo123');
  await page.locator('#kc-login').click();
  await page.locator('#app-view:not([hidden])').waitFor();
  await page.locator('#overview-content:not([hidden])').waitFor();
  await page.screenshot({ path: join(shots, 'overview-desktop.png'), fullPage: true });

  await page.locator('.nav-link[data-nav="routes"]').click();
  await page.locator('#routes-loading').waitFor({ state: 'hidden' });
  await expect(page.locator('#route-map')).toBeVisible();
  await page.locator('#map-route-select').selectOption('');
  await expect(page.locator('#view-routes')).toContainText(/mô phỏng/i);
  assert.equal(await progress(), 0, 'demo starts at zero');
  await page.locator('#map-play').click();
  await expect.poll(progress).toBeGreaterThan(0);
  await page.locator('#map-play').click();
  const paused = await progress();
  await page.waitForTimeout(350);
  assert.equal(await progress(), paused, 'paused simulation holds its position');
  await page.locator('#map-reset').click();
  assert.equal(await progress(), 0, 'reset rewinds the simulation');

  const fitted = await mapBox();
  await page.locator('#map-zoom-in').click();
  await expect.poll(mapBox).not.toBe(fitted);
  await page.locator('#map-fit').click();
  assert.equal(await mapBox(), fitted, 'fit restores the full route');
  await page.screenshot({ path: join(shots, 'map-desktop.png'), fullPage: true });

  const actualRoutes = await page.locator('#map-route-select option').evaluateAll(options =>
    options.map(option => option.value).filter(Boolean));
  if (actualRoutes.length) {
    await page.locator('#map-route-select').selectOption(actualRoutes[0]);
    await expect(page.locator('#map-stop-list')).not.toBeEmpty();
    await page.locator('#map-route-select').selectOption('');
  }
  await page.locator('#map-play').click();
  await expect.poll(progress).toBeGreaterThan(0);
  await page.locator('.nav-link[data-nav="overview"]').click();
  const hiddenProgress = await progress();
  await page.waitForTimeout(350);
  assert.equal(await progress(), hiddenProgress, 'leaving map pauses playback');

  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: join(shots, 'overview-mobile.png'), fullPage: true });
  assert.equal(await noOverflow(), true, 'overview has no mobile page overflow');
  await page.locator('.nav-link[data-nav="routes"]').click();
  await page.locator('#map-reset').click();
  await expect(page.locator('#route-map')).toBeVisible();
  assert.equal(await noOverflow(), true, 'map has no mobile page overflow');
  await page.screenshot({ path: join(shots, 'map-mobile.png'), fullPage: true });
  assert.deepEqual(writes, [], 'map demonstration must not change business data');
  assert.deepEqual(errors, [], 'browser has no runtime errors');

  // A route without authorized source coordinates must not invent an origin.
  const edgePage = await browser.newPage();
  await edgePage.setContent('<section id="edge-map"></section>');
  await edgePage.addScriptTag({ path: resolve('portal/route-map.js') });
  const edge = await edgePage.evaluate(() => {
    const root = document.querySelector('#edge-map');
    const map = new window.FreshMeshMap.RouteMap(root);
    map.update({ routes: [{ id: 'missing-origin', transfer_ids: [], stops: [
      { store_id: 'DEST', name: '<img src=x onerror=alert(1)>', lat: 10.8, lng: 106.68 },
    ] }], stores: [], transfers: [] });
    root.querySelector('#map-route-select').value = 'missing-origin';
    map.render();
    return {
      originMarkers: root.querySelectorAll('.map-origin').length,
      firstMarker: root.querySelector('.map-marker text').textContent,
      playDisabled: root.querySelector('#map-play').disabled,
      injectedImages: root.querySelectorAll('img').length,
    };
  });
  assert.equal(edge.originMarkers, 0, 'missing source must not become an origin marker');
  assert.equal(edge.firstMarker, '1', 'destination-only route starts with delivery point 1');
  assert.equal(edge.playDisabled, true, 'one point cannot animate a route');
  assert.equal(edge.injectedImages, 0, 'store labels are rendered as text');
  await edgePage.close();
  console.log(JSON.stringify({ result: 'passed', simulation: 'play/pause/reset', zoom: 'fit',
    actual_route_checked: actualRoutes.length > 0, business_writes: writes.length,
    mobile_width: 390, screenshots: shots }));
} finally {
  await browser.close();
}
