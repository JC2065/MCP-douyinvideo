const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');
test('cloud speech runtime uses pinned compatible decoder and offline model mount',()=>{
 const image=fs.readFileSync('scripts/Dockerfile.video','utf8');const compose=fs.readFileSync('compose.video-cloud.yml','utf8');
 assert.match(image,/faster-whisper==1\.1\.0/);assert.match(image,/requests==2\.32\.3/);assert.match(image,/av==17\.0\.0/);
 assert.match(compose,/YOUAI_WHISPER_MODEL: \/models\/faster-whisper-tiny/);assert.match(compose,/\.\/models:\/models:ro/);
});
