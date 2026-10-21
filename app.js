const config=require('./utils/client-config');
const service=require('./utils/video-service');
App({onLaunch(){config.refresh(wx,service.baseUrl);}});
