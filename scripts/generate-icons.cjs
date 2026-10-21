// Rebuild local PNG icons: YOUAI_PLAYWRIGHT_MODULE may point to an external Playwright installation.
const fs = require('node:fs');
const path = require('node:path');
const shapes = {
  download: '<path d="M12 3v12m-5-5 5 5 5-5M4 16v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4"/>',
  transcript: '<rect x="5" y="2" width="14" height="20" rx="3"/><path d="M9 7h6M9 11h6M9 15h6M9 19h3"/>',
  audio: '<path d="M9 17V5l11-2v12M9 9l11-2"/><ellipse cx="6" cy="18" rx="3" ry="3"/><ellipse cx="17" cy="16" rx="3" ry="3"/>',
  eraser: '<path d="m4 13 9-9a2 2 0 0 1 3 0l4 4a2 2 0 0 1 0 3l-9 9H8l-4-4a2 2 0 0 1 0-3ZM9 8l7 7M11 20h10"/>',
  cover: '<rect x="3" y="3" width="18" height="18" rx="3"/><circle cx="8" cy="8" r="1.5"/><path d="m3 17 5-5 4 4 4-6 5 7"/>',
  teleprompter: '<rect x="3" y="3" width="18" height="14" rx="3"/><path d="M8 7h8M8 11h5M12 17v4M8 21h8"/>',
  inspiration: '<path d="M9 17c0-2-4-3.5-4-8a7 7 0 0 1 14 0c0 4.5-4 6-4 8M9 17h6M9.5 20h5M11 23h2M10 9l2 3 2-3M12 12v5"/>',
  create: '<path d="M14 4H6a3 3 0 0 0-3 3v11a3 3 0 0 0 3 3h11a3 3 0 0 0 3-3v-7M9 15l1-4L18.5 2.5a2.12 2.12 0 0 1 3 3L13 14l-4 1ZM16.5 4.5l3 3"/>',
  learn: '<path d="M12 6c-3-2.5-6-3-10-2v15c4-1 7-.5 10 2 3-2.5 6-3 10-2V4c-4-1-7-.5-10 2ZM12 6v15M5.5 8.5l3 1M15.5 9.5l3-1"/>',
  tasks: '<rect x="3" y="6" width="18" height="15" rx="4"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M3 12c5 3 13 3 18 0M10 13h4v3h-4z"/>',
  profile: '<circle cx="12" cy="7" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  sparkle: '<path d="m10 3 2.5 6.5L19 12l-6.5 2.5L10 21l-2.5-6.5L1 12l6.5-2.5L10 3ZM20 2v5M17.5 4.5h5"/>',
  back: '<path d="m15 5-7 7 7 7"/>',
  chevron: '<path d="m9 5 7 7-7 7"/>',
  reset: '<path d="M4 9a8 8 0 1 1 0 6M4 3v6h6"/>',
  mic: '<rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3M8 21h8"/>',
  image: '<rect x="3" y="4" width="18" height="16" rx="3"/><circle cx="8.5" cy="9.5" r="1.6"/><path d="m4 18 5-5 3.5 3.5L15 14l5 5"/>',
};
const colors = { default: '#526176', selected: '#075dcc', white: '#ffffff' };
const nav = ['inspiration', 'create', 'learn', 'tasks', 'profile'];
const variants = Object.keys(shapes).flatMap(name => (nav.includes(name) ? ['default','selected'] : name === 'plus' ? ['white'] : ['selected']).map(state => ({name,state})));
function svg(name,state) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="-2 -2 28 28" fill="none" stroke="${colors[state]}" stroke-width="${state==='selected' ? 1.9 : 1.7}" stroke-linecap="round" stroke-linejoin="round">${shapes[name]}</svg>`;
}
async function generate() {
  const { chromium } = require(process.env.YOUAI_PLAYWRIGHT_MODULE || 'playwright');
  const browser = await chromium.launch({headless:true,channel:'msedge'});
  const directory = path.join(__dirname,'../assets/icons');
  fs.mkdirSync(directory,{recursive:true});
  try {
    const page = await browser.newPage({viewport:{width:28,height:28},deviceScaleFactor:3});
    for (const {name,state} of variants) {
      if(process.argv.length>2&&!process.argv.slice(2).includes(name))continue;
      const source=svg(name,state);
      fs.writeFileSync(path.join(directory,`${name}-${state}.svg`),source+'\n');
      await page.setContent(`<style>html,body{margin:0;background:transparent}svg{display:block}</style>${source}`);
      await page.screenshot({path:path.join(directory,`${name}-${state}.png`),omitBackground:true});
    }
  } finally { await browser.close(); }
}
module.exports={shapes,variants,svg};
if(require.main===module)generate().catch(error=>{console.error(error);process.exitCode=1;});
