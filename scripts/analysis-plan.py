"""Bounded data-only analysis instructions; questions are never evidence."""
GOALS={'structure':'学内容结构','emotion':'学情绪表达','selling':'讲清卖点','conversion':'学行动引导','trust':'看演示证据','visual':'学镜头节奏'}
TYPES=('voice','graphic','product','tutorial','story','offer')
def validate(raw):
    if raw is None:return None
    if not isinstance(raw,dict) or set(raw)-{'templateId','templateName','version','materialType','goalIds','questions','steps'}:raise ValueError('拆解模板格式无效')
    def text(value,limit):
        if not isinstance(value,str) or not value.strip() or len(value)>limit:raise ValueError('拆解模板文字无效')
        return value.strip()
    if raw.get('materialType') not in TYPES:raise ValueError('素材类型无效')
    goals=raw.get('goalIds');questions=raw.get('questions');steps=raw.get('steps')
    if not isinstance(goals,list) or not 1<=len(goals)<=6 or any(not isinstance(key,str) or key not in GOALS for key in goals):raise ValueError('拆解目标无效')
    if not isinstance(questions,list) or not 1<=len(questions)<=21 or not isinstance(steps,list) or len(steps)>12:raise ValueError('拆解栏目数量无效')
    rows=[];keys=set()
    for row in questions:
        if not isinstance(row,dict) or set(row)!= {'key','title','question'}:raise ValueError('拆解栏目格式无效')
        key=text(row.get('key'),41)
        if key in keys:raise ValueError('拆解栏目重复')
        keys.add(key);rows.append({'key':key,'title':text(row.get('title'),40),'question':text(row.get('question'),240)})
    version=raw.get('version')
    if type(version) is not int or not 1<=version<=9999:raise ValueError('模板版本无效')
    return {'templateId':text(raw.get('templateId'),48),'templateName':text(raw.get('templateName'),32),'version':version,'materialType':raw['materialType'],'goalIds':list(dict.fromkeys(goals)),'questions':rows,'steps':[text(step,240) for step in steps]}

def instruction(plan):
    if not plan:return ''
    targets='、'.join(GOALS[key] for key in plan['goalIds'])
    questions='；'.join(row['title']+'：'+row['question'] for row in plan['questions'])
    return '用户拆解模板：'+plan['templateName']+'；学习目标：'+targets+'；学习重点：'+questions+'。这些问题是创作要求，不是原片事实；仅使用已提供画面和音轨支持的信息，未核实内容不得补写成结论。'
