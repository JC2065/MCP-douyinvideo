const {loadConfig}=require('./config');
const {createPool}=require('./database');
const runner=require('./migration-runner');

async function main(command=process.argv[2]||'status'){
 if(!['up','status'].includes(command))throw Error('用法：node backend/migrate.js <up|status>');
 const pool=createPool(loadConfig());const client=await pool.connect();
 try{if(command==='up'){await runner.up(client);process.stdout.write('数据库迁移完成\n');}else process.stdout.write(JSON.stringify(await runner.status(client),null,2)+'\n');}
 finally{client.release();await pool.end();}
}
if(require.main===module)main().catch(error=>{process.stderr.write(`数据库迁移失败：${error.message}\n`);process.exitCode=1;});
module.exports={main};
