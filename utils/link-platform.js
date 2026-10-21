// Mirrors scripts/link-platform.py: which platform a pasted share text points to.
const PLATFORMS=[
 ['douyin','抖音',/https:\/\/(?:v\.|www\.|m\.)?(?:douyin|iesdouyin)\.com\/[A-Za-z0-9._~:/?#@!$&'()*+,;=%-]+/i,'douyin-v1'],
 ['kuaishou','快手',/https?:\/\/(?:v\.|www\.|m\.)?(?:kuaishou|gifshow|chenzhongtech)\.com\/[^\s]+/i,null],
 ['xiaohongshu','小红书',/https?:\/\/(?:www\.)?(?:xiaohongshu\.com|xhslink\.com)\/[^\s]+/i,null],
 ['bilibili','哔哩哔哩',/https?:\/\/(?:www\.|m\.)?(?:bilibili\.com|b23\.tv)\/[^\s]+/i,null],
 ['weixin','视频号',/https?:\/\/(?:channels\.weixin\.qq\.com|weixin\.qq\.com\/sph)\/[^\s]+/i,null]
];
function detect(text){
 text=typeof text==='string'?text:'';
 for(const [platform,name,pattern,parser] of PLATFORMS){const match=text.match(pattern);if(match){const supported=!!parser;return {platform,name,url:match[0].replace(/[.,;!?，。；！？、）》】]+$/,''),parser,supported,message:supported?'':'暂只支持抖音链接，'+name+'视频请上传原视频'};}}
 if(/https?:\/\//i.test(text))return {platform:'unknown',name:'未知平台',url:'',parser:null,supported:false,message:'暂只支持抖音链接，其他视频请上传原视频'};
 return {platform:'none',name:'',url:'',parser:null,supported:false,message:'请粘贴抖音分享链接或上传原视频'};
}
module.exports={detect};
