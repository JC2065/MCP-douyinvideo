## 改了什么

<!-- 一两句话说明改动内容和原因；关联 Issue 请写 Closes #123 -->

## 怎么验证

<!-- 跑了哪些测试；界面改动请附截图 -->

- [ ] `node --test tests/<相关文件>.test.js`
- [ ] `python3 -m unittest test-<相关模块>`（在 `scripts/` 下）

## 自查

- [ ] 没有提交密钥、令牌、数据库或 `.env`
- [ ] 新增的后端模块已加入 `scripts/Dockerfile.video`
- [ ] 改了隐私相关文案时，同步更新了 `docs/privacy-creation-board.md`
- [ ] 用户可见名称写的是「有AI」
