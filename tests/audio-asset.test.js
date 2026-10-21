const test=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
function harness(options={}) {
 const events={},updates=[],calls={downloads:0,play:0,destroy:0,shared:[]};
 const player={paused:true,currentTime:3,duration:21.2,play(){calls.play++;this.paused=false;events.play();},pause(){this.paused=true;events.pause();},destroy(){calls.destroy++;}};
 for(const event of ['Play','Pause','Ended','TimeUpdate','Error'])player['on'+event]=cb=>events[event.toLowerCase()]=cb;
 const api={env:{USER_DATA_PATH:'/user'},createInnerAudioContext:()=>player,getFileSystemManager:()=>({copyFile:o=>{calls.copy=o.destPath;o.success();}}),shareFileMessage:o=>{calls.shared.push(o);}};
 const service={downloadFile(_api,o){calls.downloads++;if(options.defer)calls.download=o;else o.success({statusCode:options.status||200,tempFilePath:'/tmp/audio'});}};
 const context={module:{exports:{}},require:()=>service};vm.runInNewContext(fs.readFileSync('utils/audio-asset.js','utf8'),context);
 const controller=context.module.exports.createAudioAsset(api,{assetUrl:'https://example.test/audio.mp3?secret',sha256:'a'.repeat(64)},value=>updates.push(value));
 return {controller,api,player,calls,events,updates};
}
test('authenticated download becomes local MP3, playback and export reuse it',async()=>{
 const h=harness();await h.controller.toggle();assert.equal(h.calls.downloads,1);assert.match(h.player.src,/^\/user\/YOUAI-.*\.mp3$/);assert.equal(h.player.obeyMuteSwitch,false);assert.equal(h.calls.play,1);
 h.events.timeupdate();assert.equal(h.updates.at(-1).audioTime,'00:03');assert.equal(h.updates.at(-1).audioDuration,'00:21');
 await h.controller.toggle();assert.equal(h.player.paused,true);await h.controller.exportFile();assert.equal(h.calls.downloads,1);assert.equal(h.calls.shared[0].filePath,h.player.src);assert.match(h.calls.shared[0].fileName,/\.mp3$/);
 h.controller.destroy();assert.equal(h.calls.destroy,1);
});
test('failed downloads cannot show success or export inaccessible files',async()=>{
 const h=harness({status:401});await h.controller.toggle();await h.controller.exportFile();assert.equal(h.calls.play,0);assert.equal(h.calls.shared.length,0);assert.match(h.updates.at(-1).error,/重新提取/);assert.equal(h.calls.downloads,2);
});
test('leaving during download suppresses stale player and UI updates',async()=>{
 const h=harness({defer:true});const pending=h.controller.toggle();h.controller.destroy();const count=h.updates.length;h.calls.download.success({statusCode:200,tempFilePath:'/tmp/audio'});await pending;assert.equal(h.calls.play,0);assert.equal(h.updates.length,count);
});
test('export cancellation is quiet; unsupported API has actionable error',async()=>{
 const h=harness();await h.controller.exportFile();const count=h.updates.length;h.calls.shared[0].fail({errMsg:'shareFileMessage:fail cancel'});assert.equal(h.updates.length,count);delete h.api.shareFileMessage;await h.controller.exportFile();assert.match(h.updates.at(-1).error,/升级微信/);
});
