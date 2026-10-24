"""Construye un candidato offline selectivo; nunca cambia ramas ni publica.

La salida es revisable y requiere respaldo real, CI y aceptación Lab antes de
copiar sus archivos a main. No importa el bot ni abre SQLite/Discord.
"""
from __future__ import annotations

import argparse
import ast
import builtins
import io
from pathlib import Path
import subprocess
import symtable
import tarfile

BASE = '41f55654a92fa44c350d2a33d261979bf595deb2'
# Solo reemplazos funcionales aprobados por #23 y sus resúmenes/editores.
REPLACE = set('''verification_atomic_setup_save personality_required
personality_allow_change clear_personality_pending_for_guild
normalize_personality_embed_text get_orientation_embed_details
get_orientation_embed_intro get_eval_role_ids build_orientation_embed
orientation_setup_summary ensure_orientation_system disable_orientation_system
classify_member_departure exit_comments_enabled exit_comment_private
exit_comment_audit_safe exit_comment_apply exit_comment_retry
exit_comment_maintenance_loop ExitCommentModal ExitCommentDMView
exit_comment_request heraldo_member_departure clear_verification_expiry
verification_is_exempt run_verification_expiry
reconcile_untracked_verifications_for_guild reconcile_untracked_verifications
check_pending_verifications evaluate_member expel render_personality_recovery_dm
send_recovery_dm verification_duration_label age_time_summary
personality_time_summary verification_hub_content AgeVerificationTimeModal
PersonalityVerificationTimeModal OrientationEmbedModal PersonalityRecoveryDMModal
HeraldoOrientationSetupView orientation_reaction_add orientation_reaction_remove
orientation_role_deleted HeraldoVerificationSetupView HeraldoVerificationHubView
ExitCommentSetupView HeraldoMemberLogSetupView handle_verify_click
evaluate_verify_timeout _evaluate_verify_timeout_inner heraldo_check_all'''.split())
REMOVE = {'HeraldoGeneralConfigModal', 'schedule_sin_verificado_check',
          'evaluate_sin_verificado'}
TESTS = '''test_verification_expiry test_verification_nh_release
test_verification_notice_persistence test_verification_reconciliation
test_verification_shared_times test_verification_staff_exemption
test_personality_copy_layout test_personality_embed_linebreaks
test_personality_recovery_dm test_personality_safety_release
test_personality_setup_contract test_personality_deadline_runtime
test_exit_comment_privacy_runtime test_member_exit_comment_flow
test_member_exit_comments'''.split()


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args])


def entries(text):
    lines = text.splitlines(keepends=True)
    result = {}
    for node in ast.parse(text).body:
        name = getattr(node, 'name', None)
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
        if name:
            start = min([node.lineno] + [n.lineno for n in getattr(node, 'decorator_list', [])]) - 1
            result[name] = (start, node.end_lineno, ''.join(lines[start:node.end_lineno]))
    return result


def globals_used(text):
    result = set()
    def visit(table):
        for symbol in table.get_symbols():
            if symbol.is_referenced() and symbol.is_global():
                result.add(symbol.get_name())
        for child in table.get_children():
            visit(child)
    visit(symtable.symtable(text, '<candidate>', 'exec'))
    return result


def once(text, before, after):
    if text.count(before) != 1:
        raise ValueError('Base changed; ambiguous selective patch: ' + before[:70])
    return text.replace(before, after, 1)


def build(root, main):
    source = (root / 'bot.py').read_text('utf-8')
    prod, dev = entries(main), entries(source)
    chosen = {name: dev[name][2] for name in REPLACE}
    # Mixed event handlers: preserve main's join-role implementation and its
    # moderation busy-key representation, which are outside this release.
    for name in ('on_member_join', 'on_member_update'):
        block = dev[name][2]
        for who, old in [('member', 'member.id'), ('after', 'after.id')]:
            for op in ('add', 'discard'):
                block = block.replace(f'_condemn_sync_busy.{op}(({who}.guild.id, {who}.id))',
                                      f'_condemn_sync_busy.{op}({old})')
        block = block.replace('(after.guild.id, after.id) in _condemn_sync_busy',
                              'after.id in _condemn_sync_busy')
        block = block.replace('queue_join_roles(member)', 'asyncio.create_task(assign_join_roles(member))')
        # Bot join roles use their separate existing production function.
        if name == 'on_member_join':
            block = block.replace('asyncio.create_task(assign_join_roles(member))',
                                  'asyncio.create_task(assign_bot_join_roles(member))', 1)
        block = block.replace('queue_join_roles(after)', 'asyncio.create_task(assign_join_roles(after))')
        chosen[name] = block
    ready = prod['on_ready'][2]
    ready = once(ready, '    db_init()\n', '    db_init()\n' +
        '    with closing(db_connect()) as conn:\n'
        '        exit_comments.init_storage(conn)\n'
        '        exit_comments.purge_expired(conn)\n'
        '    if not any(isinstance(v, ExitCommentDMView) for v in bot.persistent_views):\n'
        '        bot.add_view(ExitCommentDMView())\n'
        '    await exit_comment_retry()\n')
    ready = once(ready, '        check_pending_verifications.start()\n',
        '        check_pending_verifications.start()\n'
        '    if not reconcile_untracked_verifications.is_running():\n'
        '        reconcile_untracked_verifications.start()\n'
        '    if not exit_comment_maintenance_loop.is_running():\n'
        '        exit_comment_maintenance_loop.start()\n')
    chosen['on_ready'] = ready
    # Only reset verification clocks after a condemnation; preserve main's
    # role restoration, case card, evidence, thread and pardon implementations.
    release = prod['release_condemned_member'][2]
    start = release.index('    restored_ids = {r.id for r in restore}')
    end = release.index('    text = f"{len(restore)}', start)
    dev_release = dev['_release_condemned_member_inner'][2]
    ds = dev_release.index('    restored_ids = {r.id for r in restore}')
    de = dev_release.index('    pending_role_details = ', ds)
    chosen['release_condemned_member'] = release[:start] + dev_release[ds:de] + release[end:]
    # Import only missing helper definitions, never replace an unrelated main
    # function merely because a Pruebas helper references it.
    module_symbols = {s.get_name() for s in symtable.symtable(main, '<main>', 'exec').get_symbols()
                      if s.is_assigned() or s.is_imported() or s.is_namespace()}
    known = module_symbols | set(dir(builtins)) | {'closing', 'exit_comments'}
    chosen['DM_TEXT'] = dev['DM_TEXT'][2]
    while True:
        missing = set().union(*(globals_used(block) for block in chosen.values())) - known - chosen.keys()
        additions = missing & dev.keys()
        if not additions:
            if missing:
                raise ValueError('Unresolved candidate globals: ' + ', '.join(sorted(missing)))
            break
        for name in additions:
            chosen[name] = dev[name][2]
    chosen['_verification_expiry_inflight'] = dev['_verification_expiry_inflight'][2]
    # Insert new helpers following their original relative order, immediately
    # before main's run block. Main functions remain byte-identical elsewhere.
    new = sorted((name for name in chosen if name not in prod), key=lambda n: dev[n][0])
    lines = main.splitlines(keepends=True)
    changes = [(prod[n][0], prod[n][1], chosen[n]) for n in chosen if n in prod]
    changes += [(prod[n][0], prod[n][1], '') for n in REMOVE if n in prod]
    for start, end, text in sorted(changes, reverse=True):
        lines[start:end] = [text]
    output = ''.join(lines)
    marker = 'if __name__ == "__main__":'
    helpers = '\n\n'.join(chosen[n] for n in new)
    output = once(output, marker, helpers + '\n\n' + marker)
    output = once(output, 'import asyncio\n',
                  'import asyncio\nfrom contextlib import closing\n'
                  'import member_exit_comments as exit_comments\n')
    compile(output, '<candidate>', 'exec')
    # Prove that no unrelated production top-level definition was replaced.
    check = entries(output)
    for name in prod.keys() - chosen.keys() - REMOVE:
        if check[name][2] != prod[name][2]:
            raise ValueError('Unrelated production definition changed: ' + name)
    return output, sorted(chosen)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if git(root, 'rev-parse', 'origin/main').decode().strip() != BASE:
        raise SystemExit('Production baseline changed; reconcile before preparing candidate')
    source = git(root, 'show', BASE + ':bot.py').decode('utf-8')
    candidate, names = build(root, source)
    target = args.output.resolve()
    target.mkdir(parents=True, exist_ok=False)
    # Tracked text/code only; no local SQLite, credentials or bot execution.
    with tarfile.open(fileobj=io.BytesIO(git(root, 'archive', BASE)), mode='r:') as archive:
        for item in archive.getmembers():
            dest = (target / item.name).resolve()
            if not dest.is_relative_to(target) or not item.isfile():
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(archive.extractfile(item).read())
    (target / 'bot.py').write_text(candidate, encoding='utf-8')
    (target / 'member_exit_comments.py').write_bytes((root / 'member_exit_comments.py').read_bytes())
    for name in TESTS + ['test_safety_regressions']:
        path = Path('tests') / (name + '.py')
        (target / path).parent.mkdir(exist_ok=True)
        (target / path).write_bytes((root / path).read_bytes())
    print('OFFLINE_CANDIDATE base=' + BASE + ' selected_definitions=' + str(len(names)))
    print('NOT_PUBLISHED backup_and_lab_acceptance_required=true')


if __name__ == '__main__':
    main()
