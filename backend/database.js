const {Pool}=require('pg');

function createPool(config){
 return new Pool({connectionString:config.databaseUrl,ssl:config.databaseSsl,max:config.databasePoolMax,connectionTimeoutMillis:config.databaseTimeoutMs,statement_timeout:config.databaseTimeoutMs,application_name:'youai-api'});
}

async function probe(pool){await pool.query('select 1 as ok');}

module.exports={createPool,probe};
