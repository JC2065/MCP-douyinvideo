const videoService = require('./video-service');

function clock(seconds) {
  seconds = Math.max(0, Math.floor(Number(seconds) || 0));
  return String(Math.floor(seconds / 60)).padStart(2, '0') + ':' + String(seconds % 60).padStart(2, '0');
}

// One result owns one local file and one player. Never send a signed URL to a native player.
function createAudioAsset(api, result, update) {
  let player, pending, filePath, disposed = false;
  const fileName = 'YOUAI-' + String(result.sha256 || Date.now()).slice(0, 16) + '.mp3';
  const notify = values => { if (!disposed) update(values); };
  const failure = message => notify({audioBusy:false, audioPlaying:false, error:message});
  function localFile() {
    if (filePath) return Promise.resolve(filePath);
    if (pending) return pending;
    notify({audioBusy:true, error:''});
    pending = new Promise((resolve, reject) => videoService.downloadFile(api, {
      url:result.assetUrl,
      success(response) {
        if (response.statusCode !== 200) return reject(Error('音频下载失败，请重新提取后重试'));
        if (disposed) return reject(Error('页面已关闭'));
        const target = api.env.USER_DATA_PATH + '/' + fileName;
        api.getFileSystemManager().copyFile({srcPath:response.tempFilePath, destPath:target,
          success() { filePath=target; resolve(target); },
          fail() { reject(Error('音频保存失败，请检查手机存储空间')); }
        });
      }, fail() { reject(Error('音频下载失败，请检查网络后重试')); }
    })).finally(() => { pending=null; notify({audioBusy:false}); });
    return pending;
  }
  async function toggle() {
    if (disposed) return;
    if (player && !player.paused) { player.pause(); return; }
    try {
      const path = await localFile();
      if (disposed) return;
      if (!player) {
        if (api.setInnerAudioOption) api.setInnerAudioOption({obeyMuteSwitch:false});
        player = api.createInnerAudioContext();
        player.obeyMuteSwitch = false;
        player.onPlay(() => notify({audioPlaying:true, error:''}));
        player.onPause(() => notify({audioPlaying:false}));
        player.onEnded(() => notify({audioPlaying:false, audioTime:'00:00'}));
        player.onTimeUpdate(() => notify({audioTime:clock(player.currentTime), audioDuration:clock(player.duration)}));
        player.onError(() => failure('音频播放失败，请重新提取后重试'));
        player.src = path;
      }
      player.play();
    } catch (error) { failure(error.message); }
  }
  async function exportFile() {
    if (disposed) return;
    if (typeof api.shareFileMessage !== 'function') return failure('当前微信版本不支持导出文件，请升级微信后重试');
    try {
      const path = await localFile();
      if (disposed) return;
      api.shareFileMessage({filePath:path,fileName,
        success:() => notify({error:''}),
        fail:error => { if (!/cancel/i.test(error.errMsg || '')) failure('音频导出失败，请重试'); }
      });
    } catch (error) { failure(error.message); }
  }
  return {toggle, exportFile, pause() { if(player) player.pause(); }, destroy() {
    disposed=true;
    if(player) player.destroy();
    // The share sheet may still be reading this file; its stable SHA name avoids duplicate copies.
  }};
}
module.exports = {createAudioAsset, clock};
