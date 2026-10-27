// Copy locked local module files into a self-hosted static viewer after npm install.
import fs from 'node:fs';
const root = new URL('.',import.meta.url);
const path = p=>new URL(p,root);
const buildSrc=path('node_modules/three/build/three.module.js');
const addonsSrc=path('node_modules/three/examples/jsm');
if (!fs.existsSync(buildSrc)||!fs.existsSync(addonsSrc)) {
 throw new Error('Missing local three package; npm install must download dependencies first');
}
fs.mkdirSync(path('vendor/build'),{recursive:true});
fs.cpSync(buildSrc,path('vendor/build/three.module.js'));
fs.cpSync(addonsSrc,path('vendor/examples/jsm'),{recursive:true});
console.log('Three.js assets copied locally; the viewer can run without CDN after setup.');
