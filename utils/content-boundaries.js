const catalog=require('./platform-boundaries');
function normalize(ids){if(!Array.isArray(ids)||!ids.length)throw Error('请至少选择一个发布平台');const allowed=catalog.platforms.map(p=>p.id);if(ids.some(id=>!allowed.includes(id)))throw Error('发布平台无效');return {version:catalog.version,platforms:[...new Set(ids)].sort()};}
function rows(ids){return catalog.platforms.map(p=>({...p,selected:ids.includes(p.id)}));}
function describe(ids){const value=normalize(ids);return [...catalog.common,...catalog.platforms.filter(p=>value.platforms.includes(p.id)).flatMap(p=>p.rules.map(r=>p.name+'：'+r))];}
module.exports={catalog,normalize,rows,describe};
