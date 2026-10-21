const item=require('../utils/local-cases').find(c=>c.id===204);
const media=require('./media');
const offline=require('./offline-video');
Page(require('./study-page').create(item,force=>offline.prepare(wx,media,item.id,force),wx));
