"""Build a review-only main candidate in a NEW directory. Never deploy/push."""
import argparse
import ast
import io
from pathlib import Path
import shutil
import subprocess
import tarfile
from textwrap import dedent

BASE = '6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667'
MODULES = ('sqlite_recovery.py', 'supabase_backup.py', 'backup_job.py',
           'production_backup_scheduler.py')
HOOK = '''    # H-03 is opt-in; disabled mode does not import backup dependencies.
    if os.environ.get("HERALDO_PRODUCTION_BACKUP_ENABLED"):
        try:
            from production_backup_scheduler import start_if_authorized
            start_if_authorized(DB_PATH)
        except Exception:
            print("H03_DAILY status=BLOCKED reason=startup_preflight_failed", flush=True)
'''


def candidate_bot(source):
    anchor = '    _startup_done = True\n    print(f"El Heraldo conectado como {bot.user}")'
    if source.count(anchor) != 1:
        raise ValueError('main_hook_anchor_changed')
    result = source.replace(anchor, HOOK + anchor)
    original, candidate = ast.parse(source), ast.parse(result)
    ready = next(n for n in candidate.body if isinstance(n, ast.AsyncFunctionDef)
                 and n.name == 'on_ready')
    matches = [i for i, n in enumerate(ready.body) if isinstance(n, ast.If)
               and ast.dump(n.test) == ast.dump(ast.parse(dedent(HOOK)).body[0].test)]
    if len(matches) != 1:
        raise ValueError('unexpected_hook_count')
    del ready.body[matches[0]]
    if ast.dump(original) != ast.dump(candidate):
        raise ValueError('unrelated_bot_change')
    return result


def prepare(repo, destination, git='git'):
    repo, destination = Path(repo), Path(destination)
    # No existing destination can be overwritten, including dangling symlinks.
    destination.mkdir(parents=False, exist_ok=False)
    raw = subprocess.check_output([git, '-C', str(repo), 'archive', BASE])
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
        archive.extractall(destination, filter='data')
    bot = destination / 'bot.py'
    bot.write_text(candidate_bot(bot.read_text(encoding='utf-8')), encoding='utf-8')
    for name in MODULES:
        target = destination / name
        if target.exists():
            raise ValueError('base_already_has_h03_module')
        shutil.copyfile(repo / name, target)
    requirements = destination / 'requirements.txt'
    requirements.write_text(requirements.read_text() + '\ncryptography>=43,<47\n')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--git', default='git')
    args = parser.parse_args()
    prepare(args.repository, args.destination, args.git)
    print('H03_CANDIDATE prepared=true deployed=false base=' + BASE)
