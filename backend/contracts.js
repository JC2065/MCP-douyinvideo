const CLIENT_TYPES=Object.freeze(['wechat-mini','web','app']);
const ENTITY_TYPES=Object.freeze([
 'ideas','projects','project_versions','assets','tool_runs','learning_records','user_settings'
]);

const API_ROUTES=Object.freeze([
 ['POST','/api/v1/auth/exchange'],
 ['POST','/api/v1/auth/refresh'],
 ['POST','/api/v1/auth/logout'],
 ['GET','/api/v1/me'],
 ['GET','/api/v1/sync/changes'],
 ['POST','/api/v1/sync/operations'],
 ['GET','/api/v1/ideas'],
 ['POST','/api/v1/ideas'],
 ['GET','/api/v1/ideas/{id}'],
 ['PATCH','/api/v1/ideas/{id}'],
 ['DELETE','/api/v1/ideas/{id}'],
 ['GET','/api/v1/projects'],
 ['POST','/api/v1/projects'],
 ['GET','/api/v1/projects/{id}'],
 ['PATCH','/api/v1/projects/{id}'],
 ['POST','/api/v1/projects/{id}/versions'],
 ['GET','/api/v1/learning-records'],
 ['PUT','/api/v1/learning-records/{caseId}'],
 ['GET','/api/v1/settings'],
 ['PATCH','/api/v1/settings'],
 ['POST','/api/v1/assets/uploads'],
 ['DELETE','/api/v1/assets/{id}'],
 ['POST','/api/v1/tool-runs'],
 ['GET','/api/v1/tool-runs/{id}'],
 ['POST','/api/v1/tool-runs/{id}/retry']
]);

module.exports={CLIENT_TYPES,ENTITY_TYPES,API_ROUTES};
