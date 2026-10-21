"""Add one exact health route, preserving the existing application and rollback copy."""
import pathlib,shutil,subprocess,time
target=pathlib.Path('/etc/nginx/sites-available/jiucheng-api')
snippet=pathlib.Path('/etc/nginx/youai-health.nginx.conf')
original=target.read_text()
include='    include /etc/nginx/youai-health.nginx.conf;\n'
if include not in original:
    anchor=original.rfind('    location / {')
    if anchor<0 or anchor<original.rfind('listen 443'):raise RuntimeError('HTTPS route anchor mismatch')
    backup=target.with_name(target.name+'.youai-backup-'+str(time.time_ns()))
    shutil.copy2(target,backup)
    try:
        target.write_text(original[:anchor]+include+original[anchor:])
        subprocess.run(['nginx','-t'],check=True)
        subprocess.run(['systemctl','reload','nginx'],check=True)
    except Exception:
        shutil.copy2(backup,target)
        subprocess.run(['nginx','-t'],check=True)
        subprocess.run(['systemctl','reload','nginx'],check=True)
        raise
    print('Health route installed; rollback:',backup)
else:
    subprocess.run(['nginx','-t'],check=True)
    print('Existing YOUAI health route preserved')
