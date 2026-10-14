// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 FreshMesh-DXOS contributors
// Real services only. This exercises the UI, including the formerly broken hidden-state behavior.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { chromium } from '@playwright/test';

const base = (process.env.PORTAL_URL || 'http://localhost:3180').replace(/\/$/, '');
const browser = await chromium.launch({headless:true});
const context = await browser.newContext({viewport:{width:1440,height:1000}});
const page = await context.newPage();
page.setDefaultTimeout(20000);
const temp = await mkdtemp(join(tmpdir(),'freshmesh-ui-'));
const errors = [];
page.on('pageerror',error=>errors.push(error.message));

async function login(username) {
  await page.goto(base);
  await page.locator('#login-button').click();
  await page.locator('#username').fill(username);
  await page.locator('#password').fill(process.env.DEMO_PASSWORD || 'demo123');
  await page.locator('#kc-login').click();
  await page.locator('#app-view:not([hidden])').waitFor();
  await page.locator('#user-scope').waitFor();
  assert.equal(await page.locator('#auth-view').isVisible(),false,'login panel must disappear after SSO');
}
async function logout() {
  if (await page.locator('dialog[open]').count()) {
    await page.locator('dialog[open] [data-action="close-dialog"]').first().click();
  }
  await page.locator('#logout-button').click();
  await page.locator('#kc-logout').click();
  await page.waitForURL(base+'/');
}
async function responseFor(path,action) {
  const response = page.waitForResponse(r=>new URL(r.url()).pathname===path && r.request().method()==='POST');
  await action();
  const value = await response;
  if (!value.ok()) throw new Error(`${path}: ${value.status()} ${await value.text()}`);
  return value.json();
}
async function prompts(answers,action) {
  const handle=async dialog=>dialog.accept(answers.shift()??'');
  page.on('dialog',handle);
  try {return await action();} finally {page.off('dialog',handle);}
}

try {
  await login('manager_a1');
  await page.locator('[data-nav="transfers"]').click();
  await page.locator('#new-transfer-button').click();
  await page.locator('#form-target-store').selectOption('A-02');
  await page.locator('#form-quantity').fill('4');
  await page.locator('[name="note"]').fill('Automated browser acceptance');
  const transfer = await responseFor('/api/transfers',()=>page.locator('#transfer-form [type="submit"]').click());
  assert.equal(transfer.status,'submitted');
  await page.locator('#transfer-dialog').waitFor({state:'hidden'});
  const id=transfer.id;
  await logout();

  await login('owner_a');
  await page.locator('[data-nav="transfers"]').click();
  await page.locator(`[data-action="open-detail"][data-id="${id}"]`).click();
  const approved=await prompts(['Browser: owner approval'],()=>responseFor(`/api/transfers/${id}/approve`,
      ()=>page.locator('#detail-dialog [data-action="approve"]').click()));
  assert.equal(approved.status,'approved');
  await page.locator('#detail-dialog').waitFor({state:'hidden'});
  await page.locator('[data-nav="routes"]').click();
  await page.locator('#plan-route-button').click();
  await page.locator(`#route-transfer-options input[value="${id}"]`).check();
  await page.locator('#form-driver').selectOption('driver_a');
  const route=await responseFor('/api/routes',()=>page.locator('#route-form [type="submit"]').click());
  assert.equal(route.method,'OR-Tools');
  assert.deepEqual(route.stops.map(stop=>stop.store_id),['A-02']);
  await page.locator('#route-dialog').waitFor({state:'hidden'});
  const dispatched=await prompts([''],()=>responseFor(`/api/routes/${route.id}/dispatch`,
      ()=>page.locator(`[data-action="dispatch-route"][data-id="${route.id}"]`).click()));
  assert.equal(dispatched.status,'dispatched');
  await logout();

  await login('driver_a');
  await page.locator('[data-nav="delivery"]').click();
  const delivered=await prompts(['Browser: one unit short','3'],()=>responseFor(`/api/transfers/${id}/deliver`,
      ()=>page.locator(`[data-action="deliver"][data-id="${id}"]`).click()));
  assert.equal(delivered.actual_quantity,3);
  assert.equal(delivered.status,'delivered');
  await logout();

  await login('manager_a2');
  await page.locator('[data-nav="delivery"]').click();
  const received=await prompts(['Browser: accept actual delivery','3'],()=>responseFor(`/api/transfers/${id}/receive`,
      ()=>page.locator(`[data-action="receive"][data-id="${id}"]`).click()));
  assert.equal(received.received_quantity,3);
  assert.equal(received.status,'received');
  await page.locator('[data-nav="transfers"]').click();
  await page.locator(`[data-action="open-detail"][data-id="${id}"]`).click();
  await page.locator('#detail-dialog[open]').waitFor();
  await page.locator('#transfer-detail-content').getByText('Đã nhận',{exact:true}).waitFor();
  const contents='FreshMesh browser evidence: 4 dispatched, 3 received. Synthetic demo.\n';
  const receipt=join(temp,'browser-receipt.txt');
  await writeFile(receipt,contents);
  await page.locator('#document-upload').setInputFiles(receipt);
  await page.locator('[data-action="download-doc"]').waitFor();
  const downloadPromise=page.waitForEvent('download');
  await page.locator('[data-action="download-doc"]').click();
  const download=await downloadPromise;
  const downloaded=join(temp,'download.txt');
  await download.saveAs(downloaded);
  assert.equal(createHash('sha256').update(await readFile(downloaded)).digest('hex'),
               createHash('sha256').update(contents).digest('hex'),'UI evidence download integrity');
  await page.locator('#detail-dialog [data-action="close-dialog"]').click();
  await page.locator('.nav-link[data-nav="health"]').click();
  await page.getByText('4/4 lõi sẵn sàng',{exact:true}).waitFor();
  await page.setViewportSize({width:390,height:844});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'mobile overflow');
  assert.deepEqual(errors,[],'browser runtime errors');
  console.log(JSON.stringify({result:'passed',transfer_id:id,route_id:route.id,
    requested:4,delivered:3,received:3,roles:['manager_a1','owner_a','driver_a','manager_a2'],
    oidc:'Authorization Code + PKCE S256',document_sha256_verified:true,mobile_width:390}));
} finally {
  await browser.close();
  await rm(temp,{recursive:true,force:true});
}
