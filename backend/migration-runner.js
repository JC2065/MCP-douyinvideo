const fs=require('node:fs');
const path=require('node:path');

function discover(directory=path.join(__dirname,'migrations')){
 const files=fs.readdirSync(directory).filter(name=>/^\d{3}_[a-z0-9_]+\.(up|down)\.sql$/.test(name));const grouped=new Map();
 for(const file of files){const match=file.match(/^(\d{3}_[a-z0-9_]+)\.(up|down)\.sql$/),item=grouped.get(match[1])||{version:match[1]};item[match[2]]=fs.readFileSync(path.join(directory,file),'utf8');grouped.set(match[1],item);}
 const migrations=[...grouped.values()].sort((a,b)=>a.version.localeCompare(b.version));
 for(const item of migrations)if(!item.up||!item.down)throw Error(`迁移 ${item.version} 必须同时提供 up 和 down`);
 return migrations;
}

async function prepare(client){await client.query('create table if not exists schema_migrations (version text primary key, applied_at timestamptz not null default now())');}
async function status(client,migrations=discover()){
 await prepare(client);const applied=new Set((await client.query('select version from schema_migrations order by version')).rows.map(row=>row.version));return migrations.map(item=>({version:item.version,applied:applied.has(item.version)}));
}
async function up(client,migrations=discover()){
 await client.query("select pg_advisory_lock(hashtext('youai_schema_migrations'))");
 try{await prepare(client);const applied=new Set((await client.query('select version from schema_migrations')).rows.map(row=>row.version));for(const item of migrations){if(applied.has(item.version))continue;await client.query('begin');try{await client.query(item.up);await client.query('insert into schema_migrations(version) values ($1)',[item.version]);await client.query('commit');}catch(error){await client.query('rollback');throw error;}}}
 finally{await client.query("select pg_advisory_unlock(hashtext('youai_schema_migrations'))");}
}

module.exports={discover,status,up};
