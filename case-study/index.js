const item=require('../utils/case87');
const video=require('./video-source');
Page(require('./study-page').create(item,force=>video.prepare(wx,force),wx));
