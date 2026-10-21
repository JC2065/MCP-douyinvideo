"""Apply the optional memory-only cache switch to DailyHotApi 2.0.8."""
import sys
from pathlib import Path

path = Path(sys.argv[1]) / 'src/utils/cache.ts'
source = path.read_text(encoding='utf-8')
old = '  if (isRedisTried) return;'
new = '  if (process.env.REDIS_DISABLED === "true" || isRedisTried) return;'
assert old in source, 'Unexpected upstream cache implementation'
source = source.replace(old, new)
old = '    await redis.del(key);'
new = '    if (process.env.REDIS_DISABLED !== "true") await redis.del(key);'
assert old in source, 'Unexpected upstream delete implementation'
path.write_text(source.replace(old, new), encoding='utf-8')
