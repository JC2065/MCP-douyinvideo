// Day feed: what the calendar view shows when scrolling past the month grid.
// Dates come from real timestamps only; entries without one are grouped under
// 'unknown' so the app never invents a day for old data.
const cal = require('./idea-calendar');

function stamp(value) {
  return typeof value === 'number' && Number.isFinite(value) && value >= 946684800000 && value <= Date.now()
    ? cal.dayKey(value) : '';
}
function workDay(work) { return stamp(work.updatedAt) || stamp(work.createdAt) || stamp(work.id); }
function assetDay(asset) {
  let value=Number(asset.time||asset.updatedAt||asset.createdAt);
  if(value>0&&value<100000000000)value*=1000;
  return stamp(value);
}

function build(state = {}, cases = [], day = cal.dayKey(), assets = []) {
  const at = state.favoriteAt || {};
  const byId = id => cases.find(c => c.id === id);
  const favoritesOf = withDate => (state.favorites || [])
    .map(byId)
    .filter(c => c && (withDate ? at[c.id] === day : !at[c.id]));
  if (day === 'unknown') {
    const works = (state.works || []).filter(w => !workDay(w));
    const datedAssets = (assets||[]).filter(a => !assetDay(a));
    const favorites = favoritesOf(false);
    return { day, ideas: [], works, assets:datedAssets, favorites, total: works.length + datedAssets.length + favorites.length };
  }
  const ideas = (state.ideas || []).filter(i => cal.ideaDay(i) === day);
  const works = (state.works || []).filter(w => workDay(w) === day);
  const dayAssets=(assets||[]).filter(a=>assetDay(a)===day);
  const favorites = favoritesOf(true);
  return { day, ideas, works, assets:dayAssets, favorites, total: ideas.length + works.length + dayAssets.length + favorites.length };
}

module.exports = { build, workDay, assetDay };
