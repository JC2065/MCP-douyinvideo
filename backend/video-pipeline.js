const {createHash}=require('node:crypto');

const REFERENCE_MODES=Object.freeze(['reference-video','content-structure','visual-style','same-topic']);
const JOB_STATES=Object.freeze(['draft','queued','running','succeeded','failed','cancelled']);
const JOB_TRANSITIONS=Object.freeze({
 draft:['queued','cancelled'],queued:['running','failed','cancelled'],running:['succeeded','failed','cancelled'],
 succeeded:[],failed:['queued','cancelled'],cancelled:[]
});

function stableHash(buffer){return createHash('sha256').update(buffer).digest('hex');}
function assertReferenceMode(mode){if(!REFERENCE_MODES.includes(mode))throw Error('INVALID_REFERENCE_MODE');return mode;}
function transitionJob(current,next){
 if(!JOB_STATES.includes(current)||!JOB_STATES.includes(next))throw Error('INVALID_JOB_STATE');
 if(!JOB_TRANSITIONS[current].includes(next))throw Error(`INVALID_JOB_TRANSITION:${current}->${next}`);
 return next;
}
function normalizeCost(value={}){
 const estimated=Number(value.estimatedCny||0),actual=value.actualCny==null?null:Number(value.actualCny);
 if(!Number.isFinite(estimated)||estimated<0||actual!==null&&(!Number.isFinite(actual)||actual<0))throw Error('INVALID_COST');
 return {estimatedCny:Number(estimated.toFixed(4)),actualCny:actual===null?null:Number(actual.toFixed(4)),currency:'CNY'};
}
function sanitizeProviderRequest(value){
 const blocked=/^(authorization|token|api[_-]?key|secret|password)$/i;
 if(Array.isArray(value))return value.map(sanitizeProviderRequest);
 if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).filter(([key])=>!blocked.test(key)).map(([key,item])=>[key,sanitizeProviderRequest(item)]));
 return value;
}
function artifactLineage({sourceAssetIds=[],analysisId=null,storyboardId=null,shotId=null,generationJobId=null,provider=null,model=null,promptVersion=null}={}){
 const ids=[...new Set(sourceAssetIds.map(String).filter(Boolean))];
 if(!ids.length)throw Error('SOURCE_ASSET_REQUIRED');
 return {sourceAssetIds:ids,analysisId,storyboardId,shotId,generationJobId,provider,model,promptVersion};
}

module.exports={REFERENCE_MODES,JOB_STATES,JOB_TRANSITIONS,stableHash,assertReferenceMode,transitionJob,normalizeCost,sanitizeProviderRequest,artifactLineage};
