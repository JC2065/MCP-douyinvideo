// 每日一拆：按视频形式分类，每天从该形式中确定性轮换一个案例。
// 规则：同一天同一形式必得同一案例；跨天轮换；某形式无案例返回 null（页面显示整理中）。
const FORMS = ['纯文字型', '图文型', '动图视频', '空镜头视频', '人物出镜'];

// 中国时区的「第几天」，保证每日零点（北京时间）切换推荐。
function dayIndex(date) {
  const t = (date ? new Date(date) : new Date()).getTime() + 8 * 3600 * 1000;
  return Math.floor(t / 86400000);
}

function byForm(cases, form) {
  return (cases || []).filter(c => c && c.form === form);
}

function pick(cases, form, date) {
  const list = byForm(cases, form);
  if (!list.length) return null;
  return list[dayIndex(date) % list.length];
}

// 默认选中第一个有案例的形式，避免用户先看到空状态。
function defaultForm(cases) {
  return FORMS.find(f => byForm(cases, f).length > 0) || FORMS[0];
}

module.exports = { FORMS, dayIndex, byForm, pick, defaultForm };
