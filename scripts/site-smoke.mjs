// SPDX-License-Identifier: Apache-2.0
// Copyright 2026 FreshMesh-DXOS contributors
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { chromium } from '@playwright/test';

const base=(process.env.SITE_URL || 'http://localhost:3181').replace(/\/$/,'');
const output=resolve(process.env.SCREENSHOT_DIR || 'dist/screenshots');
await mkdir(output,{recursive:true});
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const errors=[];
page.on('pageerror',error=>errors.push(error.message));
const license='SPDX-License-Identifier: Apache-2.0\nSPDX-FileCopyrightText: 2026 FreshMesh-DXOS contributors\nOriginal rendered FreshMesh artwork or real static website capture. App images are real Playwright synthetic-data evidence.\n';
async function screenshot(name) {
  await page.screenshot({path:join(output,`${name}.png`),fullPage:true});
  await writeFile(join(output,`${name}.png.license`),license);
}
try {
  for(const width of [1440,390]) {
    await page.setViewportSize({width,height:width===390?844:1000});
    const response=await page.goto(base,{waitUntil:'networkidle'});
    assert.equal(response.status(),200);
    await page.evaluate(()=>document.fonts.ready);
    await page.getByRole('heading',{level:1}).waitFor();
    for(const image of await page.locator('img').all()) {
      await image.scrollIntoViewIfNeeded();
      await image.evaluate(image=>new Promise((resolve,reject)=>{
        if(image.complete) return image.naturalWidth?resolve():reject(new Error(`image failed: ${image.src}`));
        image.addEventListener('load',resolve,{once:true});
        image.addEventListener('error',()=>reject(new Error(`image failed: ${image.src}`)),{once:true});
      }));
    }
    const targets=await page.locator('a[href^="#"]').evaluateAll(links=>links.map(link=>link.getAttribute('href')));
    for(const target of targets.filter(target=>target!=='#')) {
      assert.equal(await page.locator(target).count(),1,`missing anchor ${target}`);
    }
    await page.getByRole('link',{name:'Chạy dự án của bạn'}).click();
    assert.equal(new URL(page.url()).hash,'#start');
    await page.getByRole('heading',{name:'Từ mã nguồn đến lần giao đầu tiên.'}).waitFor();
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`overflow at ${width}`);
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.emulateMedia({reducedMotion:'reduce'});
    await screenshot(width===390?'landing-mobile':'landing-desktop');
  }
  await page.setViewportSize({width:1440,height:440});
  const banner=await page.goto(`${base}/assets/banner.svg`,{waitUntil:'networkidle'});
  assert.equal(banner.status(),200);
  await page.locator('svg').screenshot({path:join(output,'banner.png')});
  await writeFile(join(output,'banner.png.license'),license);
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({result:'passed',site:base,viewports:[1440,390],images:'loaded',navigation:'#start',banner:'rendered original SVG'}));
} finally {await browser.close();}
