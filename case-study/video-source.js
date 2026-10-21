// Single offline demo adapter. Production should resolve HTTPS CDN URLs.
const offline=require('./offline-video');
function prepare(api,force=false){return offline.prepare(api,require('./assets/video87'),87,force);}
module.exports={prepare};
