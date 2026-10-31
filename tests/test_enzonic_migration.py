"""Restauración/cifrado reales con SQLite sintética y transporte HTTP simulado.

Estas pruebas NO acreditan ejecución en Enzonic, Supabase real ni Discord.
"""
import asyncio
import base64
from contextlib import closing, redirect_stdout
from datetime import datetime, timezone
import hashlib
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import backup_job as job
import enzonic_test_backup as worker
import enzonic_test_host as host
import restore_enzonic_test as restore
import sqlite_recovery as recovery
import supabase_backup as cloud
import test_backup_scheduler as scheduler


class EnzonicFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'container'
        self.root.mkdir()
        self.db, self.state = self.root / 'heraldo.db', self.root / '.heraldo-h03-enzonic'
        uid = '11111111-1111-4111-8111-111111111111'
        env = dict(HERALDO_HOSTING_PROVIDER='enzonic', HERALDO_ENVIRONMENT='heraldo-test',
                   DB_PATH=str(self.db), SUPABASE_BACKUP_URL=host.SUPABASE_URL,
                   SUPABASE_BACKUP_PUBLISHABLE_KEY='sb_publishable_fixture',
                   SUPABASE_BACKUP_EMAIL='fixture@example.invalid',
                   SUPABASE_BACKUP_PASSWORD='fixture', SUPABASE_BACKUP_USER_ID=uid,
                   HERALDO_BACKUP_ENCRYPTION_KEY=base64.b64encode(b'x'*32).decode())
        self.env = patch.dict(os.environ, env, clear=True)
        self.env.start(); self.addCleanup(self.env.stop)
        # También simular la ubicación: la ruta real /home/container activa la
        # detección de Enzonic incluso al vaciar el entorno para simular Railway.
        source_patch = patch.object(host, '__file__', str(self.root / 'enzonic_test_host.py'))
        source_patch.start(); self.addCleanup(source_patch.stop)
        for name, value in (('ROOT', self.root), ('DATABASE', self.db), ('STATE', self.state),
                            ('TEST_UID_SHA256', hashlib.sha256(uid.encode()).hexdigest())):
            p = patch.object(host, name, value); p.start(); self.addCleanup(p.stop)
        p=patch.object(restore, 'DESTINATION', self.db); p.start(); self.addCleanup(p.stop)
        p=patch.object(Path, 'is_mount', return_value=True); p.start(); self.addCleanup(p.stop)
        self.git_patch=patch.object(host, 'revision', return_value='a'*40)
        self.git_patch.start(); self.addCleanup(self.git_patch.stop)
        self.objects={}; self.uploads=0; self.gets=0
        jwt_payload=base64.urlsafe_b64encode(json.dumps({'sub':uid}).encode()).decode().rstrip('=')
        self.jwt='fixture.'+jwt_payload+'.fixture'
        p=patch.object(cloud, '_http', side_effect=self.http); p.start(); self.addCleanup(p.stop)
        p=patch.object(worker, '_http', side_effect=self.http); p.start(); self.addCleanup(p.stop)

    def http(self, url, *, method, headers, payload=None, limit=None):
        if '/auth/v1/' in url:
            return json.dumps({'access_token':self.jwt}).encode()
        if url.endswith('/users/@me'):
            return json.dumps({'id':'123456789012345678', 'bot':True,
                               'username':"El Heraldo's Lab 🧪",'discriminator':'6700'}).encode()
        self.assertIn('Authorization', headers)
        if '/object/list/' in url:
            prefix=json.loads(payload)['prefix']
            if prefix=='heraldo-test':
                return json.dumps([{'name':day,'id':None} for day in sorted({o.split('/')[1] for o in self.objects})]).encode()
            return json.dumps([{'name':key.split('/')[-1], 'id':'fixture', 'metadata':{'size':len(blob)}}
                               for key,blob in self.objects.items() if key.startswith(prefix+'/')]).encode()
        self.assertIn('/object/heraldo-test-sqlite-backups/', url)
        key=url.split('/object/heraldo-test-sqlite-backups/')[1]
        if method=='POST':
            self.assertEqual(headers['x-upsert'],'false')
            self.assertNotIn(key,self.objects)
            self.objects[key]=payload; self.uploads+=1
            return b'{}'
        self.gets+=1
        return self.objects[key]

    def persist(self):
        with patch.object(host,'runtime_instance',side_effect=['old-instance','new-instance']):
            self.assertEqual(host.persistence_probe('prepare'),'RESTART_REQUIRED')
            self.assertEqual(host.persistence_probe('verify'),'VERIFIED_AFTER_RESTART')

    def live(self):
        self.persist()
        with closing(sqlite3.connect(self.db)) as db:
            db.executescript('CREATE TABLE parent(id INTEGER PRIMARY KEY);'
                             'CREATE TABLE child(id INTEGER REFERENCES parent(id), value TEXT);'
                             "INSERT INTO parent VALUES(1); INSERT INTO child VALUES(1,'historical');")
        os.chmod(self.db,0o600)
        host.write_receipt('migration.json',{'status':'verified_and_installed',
                           'environment':host.ENVIRONMENT,'sqlite_sha256':recovery.digest(self.db),
                           'schema_sha256':recovery.inspect_database(self.db)['schema_sha256']})

    def generation(self):
        source=self.root/'original.sqlite'
        with closing(sqlite3.connect(source)) as db:
            db.executescript("CREATE TABLE historical(id INTEGER PRIMARY KEY, value TEXT);"
                             "INSERT INTO historical VALUES(1,'original');")
        package=recovery.create_backup(source,self.root/'source-packages',
                                       environment='heraldo-test',revision='b'*40)
        blob,manifest=cloud._bundle(package,'heraldo-test',cloud._key())
        name='heraldo-test/'+manifest['created_at'][:10].replace('-','')+'/'+'c'*32+'.h03e'
        self.objects[name]=blob
        return name,manifest


class RecoverySafety(EnzonicFixture):
    def test_full_authenticated_recovery_preserves_content_and_installs_private(self):
        self.persist(); name,manifest=self.generation()
        os.environ['HERALDO_TEST_RECOVERY_OBJECT']=name
        original=dict(self.objects)
        out=StringIO()
        with redirect_stdout(out): self.assertEqual(restore.main(),0)
        self.assertEqual(recovery.digest(self.db),manifest['sha256'])
        with closing(recovery.readonly(self.db)) as db:
            self.assertEqual(db.execute('SELECT value FROM historical').fetchall(),[('original',)])
        self.assertEqual(self.db.stat().st_mode&0o777,0o600)
        self.assertEqual(self.objects,original)
        host.require_restored_database()
        self.assertNotIn('original',out.getvalue())

    def test_active_bot_lock_blocks_before_download_or_install(self):
        self.persist(); name,_=self.generation(); os.environ['HERALDO_TEST_RECOVERY_OBJECT']=name
        with recovery.service_lock(self.db), redirect_stdout(StringIO()):
            self.assertEqual(restore.main(),1)
        self.assertEqual(self.gets,0); self.assertFalse(self.db.exists())

    def test_existing_database_never_overwritten(self):
        self.live(); name,_=self.generation(); os.environ['HERALDO_TEST_RECOVERY_OBJECT']=name
        before=self.db.read_bytes()
        with redirect_stdout(StringIO()): self.assertEqual(restore.main(),1)
        self.assertEqual(self.db.read_bytes(),before); self.assertEqual(self.gets,0)

    def test_empty_disabled_and_enabled_legacy_flag_all_block(self):
        self.persist(); name,_=self.generation(); os.environ['HERALDO_TEST_RECOVERY_OBJECT']=name
        for value in ('','disabled','enabled'):
            with self.subTest(value=value),patch.dict(os.environ,HERALDO_TEST_BACKUP_ENABLED=value):
                with self.assertRaisesRegex(restore.MigrationBlocked,'PLANIFICADOR_ANTIGUO'):
                    restore._preflight()

    def test_dangling_sidecar_blocks(self):
        self.persist(); name,_=self.generation(); os.environ['HERALDO_TEST_RECOVERY_OBJECT']=name
        Path(str(self.db)+'-wal').symlink_to(self.root/'missing')
        with self.assertRaisesRegex(restore.MigrationBlocked,'ARCHIVOS_SQLITE_EXISTENTES'):
            restore._preflight()

    def test_wrong_aes_key_never_installs_empty_replacement(self):
        self.persist(); name,_=self.generation(); os.environ['HERALDO_TEST_RECOVERY_OBJECT']=name
        os.environ['HERALDO_BACKUP_ENCRYPTION_KEY']=base64.b64encode(b'z'*32).decode()
        out=StringIO()
        with redirect_stdout(out): self.assertEqual(restore.main(),1)
        self.assertFalse(self.db.exists()); self.assertIn('decryption_or_integrity_failed',out.getvalue())

    def test_tampered_ciphertext_never_installs(self):
        self.persist(); name,_=self.generation(); os.environ['HERALDO_TEST_RECOVERY_OBJECT']=name
        self.objects[name]=self.objects[name][:-1]+bytes([self.objects[name][-1]^1])
        with redirect_stdout(StringIO()): self.assertEqual(restore.main(),1)
        self.assertFalse(self.db.exists())

    def test_production_object_rejected_before_network(self):
        self.persist(); os.environ['HERALDO_TEST_RECOVERY_OBJECT']='heraldo-production/20261029/'+'c'*32+'.h03e'
        with self.assertRaisesRegex(restore.MigrationBlocked,'RESPALDO_TEST_NO_SELECCIONADO'):
            restore._preflight()
        self.assertEqual(self.gets,0)


class HostSafety(EnzonicFixture):
    def test_real_container_path_rejects_railway_identity_before_gateway(self):
        with patch.object(host, '__file__', '/home/container/enzonic_test_host.py'):
            for project in (host.TEST_PROJECT, job.PRODUCTION_IDS[0]):
                with self.subTest(project=project), patch.dict(os.environ,
                        {'RAILWAY_PROJECT_ID': project}, clear=True):
                    self.assertTrue(host.is_enzonic())
                    self.assertFalse(host.is_test())
                    with self.assertRaisesRegex(job.BackupJobError, 'enzonic_identity_mismatch'):
                        host.before_discord()
        self.assertFalse(self.db.exists())

    def test_missing_provider_on_real_container_path_fails_before_sqlite_creation(self):
        os.environ.pop('HERALDO_HOSTING_PROVIDER')
        with patch.object(host,'__file__','/home/container/enzonic_test_host.py'):
            self.assertTrue(host.is_enzonic())
            with self.assertRaisesRegex(job.BackupJobError,'enzonic_identity_mismatch'):
                host.before_discord()
        self.assertFalse(self.db.exists())

    def test_old_test_start_stops_before_gateway_without_affecting_production(self):
        with patch.dict(os.environ,{'RAILWAY_PROJECT_ID':host.TEST_PROJECT},clear=True),redirect_stdout(StringIO()):
            with self.assertRaises(SystemExit) as result:
                host.refuse_legacy_test_start()
            self.assertEqual(result.exception.code,0)
        with patch.dict(os.environ,{'RAILWAY_PROJECT_ID':job.PRODUCTION_IDS[0]},clear=True):
            host.refuse_legacy_test_start()

    def test_real_restart_required_and_probe_not_overwritten(self):
        with patch.object(host,'runtime_instance',return_value='same'):
            host.persistence_probe('prepare')
            before=(self.state/'persistence.json').read_bytes()
            with self.assertRaisesRegex(job.BackupJobError,'container_restart_not_observed'):
                host.persistence_probe('verify')
            with self.assertRaisesRegex(job.BackupJobError,'persistence_probe_already_exists'):
                host.persistence_probe('prepare')
            self.assertEqual((self.state/'persistence.json').read_bytes(),before)

    def test_all_railway_variables_are_rejected(self):
        with patch.dict(os.environ,RAILWAY_PROJECT_ID=host.TEST_PROJECT):
            with self.assertRaisesRegex(job.BackupJobError,'stale_railway_variables'):
                host.provider_preflight()

    def test_fake_mount_rejected(self):
        with patch.object(Path,'is_mount',return_value=False):
            with self.assertRaisesRegex(job.BackupJobError,'persistent_mount_missing'):
                host.provider_preflight()

    def test_production_secret_identity_rejected(self):
        with patch.dict(os.environ,SUPABASE_BACKUP_USER_ID='22222222-2222-4222-8222-222222222222'):
            with self.assertRaisesRegex(job.BackupJobError,'test_storage_identity_mismatch'):
                host.check_test_secrets()

    def test_service_role_key_rejected(self):
        payload=base64.urlsafe_b64encode(b'{"role":"service_role"}').decode().rstrip('=')
        with patch.dict(os.environ,SUPABASE_BACKUP_PUBLISHABLE_KEY='x.'+payload+'.x'):
            with self.assertRaisesRegex(job.BackupJobError,'privileged_test_key_forbidden'):
                host.check_test_secrets()

    def test_missing_migration_never_creates_database_on_startup(self):
        self.persist()
        with self.assertRaises(job.BackupJobError): host.before_discord()
        self.assertFalse(self.db.exists())

    def test_token_checked_without_gateway_and_wrong_account_rejected(self):
        os.environ['DISCORD_TOKEN']='synthetic-secret'
        host.verify_test_token()
        with patch.object(cloud,'_http',return_value=b'{"id":"123456789012345678","bot":true,"username":"El Heraldo","discriminator":"0000"}'):
            with self.assertRaisesRegex(job.BackupJobError,'wrong_discord_bot'):
                host.verify_test_token()

    def test_receipt_symlink_rejected(self):
        self.state.mkdir(mode=0o700)
        (self.state/'migration.json').symlink_to(self.root/'outside')
        with self.assertRaises(job.BackupJobError): host.read_receipt('migration.json')

    def test_disk_budget_counts_code_and_dependencies(self):
        self.state.mkdir(mode=0o700)
        (self.root/'dependency.bin').write_bytes(b'x'*200)
        with patch.object(host,'DISK_CAP_BYTES',300):
            self.assertEqual(host.remaining_space(self.state),100)

    def test_test_identity_survives_provider_move(self):
        self.assertTrue(host.is_test())
        with patch.dict(os.environ,HERALDO_ENVIRONMENT='heraldo-production'):
            self.assertFalse(host.is_test())
        with patch.dict(os.environ,{'RAILWAY_PROJECT_ID':host.TEST_PROJECT},clear=True):
            self.assertTrue(host.is_test())
        with patch.dict(os.environ,{'RAILWAY_PROJECT_ID':job.PRODUCTION_IDS[0]},clear=True):
            self.assertFalse(host.is_test())

    def test_revision_uses_real_checkout_and_rejects_dirty_tree_or_main(self):
        self.git_patch.stop()
        subprocess.run(['git','init','-q','-b','Pruebas',str(self.root)],check=True)
        (self.root/'marker').write_text('safe')
        subprocess.run(['git','-C',str(self.root),'add','marker'],check=True)
        subprocess.run(['git','-C',str(self.root),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid',
                        'commit','-qm','fixture'],check=True)
        self.assertRegex(host.revision(),r'^[0-9a-f]{40}$')
        (self.root/'marker').write_text('changed')
        with patch.object(host, '_github_metadata', side_effect=job.BackupJobError('enzonic_checkout_unverified')):
            with self.assertRaisesRegex(job.BackupJobError,'checkout_unverified'):
                host.revision()
        (self.root/'marker').write_text('safe')
        subprocess.run(['git','-C',str(self.root),'branch','-m','main'],check=True)
        with self.assertRaisesRegex(job.BackupJobError,'wrong_branch'): host.revision()


    def test_github_deploy_overlay_verified_against_exact_remote_tree(self):
        """HEAD viejo: se acepta solo si TODOS los archivos coinciden con Pruebas."""
        self.git_patch.stop()
        subprocess.run(['git', 'init', '-q', '-b', 'Pruebas', str(self.root)], check=True)
        (self.root / 'bot.py').write_bytes(b'old program\\n')
        (self.root / 'enzonic_test_host.py').write_bytes(b'old guard\\n')
        subprocess.run(['git', '-C', str(self.root), 'add', 'bot.py', 'enzonic_test_host.py'], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Fixture',
                        '-c', 'user.email=fixture@example.invalid',
                        'commit', '-qm', 'fixture'], check=True)
        local = host.revision()
        (self.root / 'bot.py').write_bytes(b'updated program\\n')
        (self.root / 'enzonic_test_host.py').write_bytes(b'updated guard\\n')
        remote = 'b' * 40
        tree_id = 'c' * 40

        def manifest():
            return {'sha': tree_id, 'truncated': False, 'tree': [
                {'path': path, 'type': 'blob', 'mode': '100644',
                 'sha': host._git_blob_sha(self.root / path, (self.root / path).stat().st_size),
                 'size': (self.root / path).stat().st_size}
                for path in ('bot.py', 'enzonic_test_host.py')]}

        # El manifiesto queda inmóvil durante el ensayo, aunque cambie el disco.
        tree = manifest()
        with patch.object(host, '_github_metadata', side_effect=[
            {'sha': remote, 'commit': {'tree': {'sha': tree_id}}}, tree
        ]) as fetch:
            self.assertEqual(host.revision(), remote)
            self.assertEqual(fetch.call_count, 2)
        self.assertNotEqual(local, remote)
        # Una modificación no publicada y un archivo ausente bloquean el arranque.
        (self.root / 'bot.py').write_bytes(b'unauthorized change\\n')
        with patch.object(host, '_github_metadata', side_effect=[
            {'sha': remote, 'commit': {'tree': {'sha': tree_id}}}, tree
        ]):
            with self.assertRaisesRegex(job.BackupJobError, 'enzonic_checkout_unverified'):
                host.revision()
        (self.root / 'bot.py').unlink()
        with patch.object(host, '_github_metadata', side_effect=[
            {'sha': remote, 'commit': {'tree': {'sha': tree_id}}}, tree
        ]):
            with self.assertRaisesRegex(job.BackupJobError, 'enzonic_checkout_unverified'):
                host.revision()

    def test_remote_manifest_invalid_or_incomplete_stays_blocked(self):
        self.git_patch.stop()
        subprocess.run(['git', 'init', '-q', '-b', 'Pruebas', str(self.root)], check=True)
        (self.root / 'marker').write_text('old')
        subprocess.run(['git', '-C', str(self.root), 'add', 'marker'], check=True)
        subprocess.run(['git', '-C', str(self.root), '-c', 'user.name=Fixture',
                        '-c', 'user.email=fixture@example.invalid',
                        'commit', '-qm', 'fixture'], check=True)
        (self.root / 'marker').write_text('updated')
        sha = 'd' * 40
        for remote_tree in (
            {'sha': 'c' * 40, 'truncated': True, 'tree': []},
            {'sha': 'c' * 40, 'truncated': False, 'tree': []},
            {'sha': 'c' * 40, 'truncated': False, 'tree': [
                {'path': '../bot.py', 'type': 'blob', 'mode': '100644', 'sha': sha, 'size': 3}]},
        ):
            with self.subTest(tree=remote_tree), patch.object(host, '_github_metadata', side_effect=[
                {'sha': sha, 'commit': {'tree': {'sha': 'c' * 40}}}, remote_tree
            ]):
                with self.assertRaisesRegex(job.BackupJobError, 'enzonic_checkout_unverified'):
                    host.revision()


class BackupSafety(EnzonicFixture):
    def test_old_uncertain_receipt_blocks_adoption_and_new_uploads(self):
        self.live(); self.generation(); worker.validate()
        host.write_receipt('heraldo-test-20200101.json',{'status':'needs_manual_review'})
        os.environ[host.FLAG]=host.FLAG_VALUE
        with self.assertRaisesRegex(job.BackupJobError,'previous_attempt_needs_review'):
            worker.due(datetime.now(timezone.utc).replace(hour=7))
        self.assertEqual(self.uploads,1)

    def test_wal_growth_is_included_in_memory_budget(self):
        self.live()
        with closing(sqlite3.connect(self.db)) as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('PRAGMA wal_autocheckpoint=0')
            db.execute('INSERT INTO child VALUES(1, zeroblob(1000000))'); db.commit()
            with patch.object(worker,'MAX_SOURCE_BYTES',500000):
                with self.assertRaisesRegex(job.BackupJobError,'source_exceeds_memory_budget'):
                    worker.configure()

    def test_full_encrypted_roundtrip_and_repeated_validation_downloads_only(self):
        self.live(); before=self.db.read_bytes()
        self.assertEqual(worker.validate(),'verified_and_restored')
        self.assertEqual(worker.validate(),'verified_and_restored')
        self.assertEqual(self.uploads,1); self.assertEqual(self.db.read_bytes(),before)
        worker.require_validation()
        self.assertFalse(list(self.state.glob('recovery-*')))

    def test_uncertain_upload_does_not_retry_and_can_reconcile(self):
        self.live()
        def lost(url,**kwargs):
            result=self.http(url,**kwargs)
            if kwargs['method']=='POST' and '/object/heraldo-test-sqlite-backups/' in url:
                raise TimeoutError('PRIVATE')
            return result
        with patch.object(cloud,'_http',side_effect=lost):
            with self.assertRaises(TimeoutError): worker.validate()
        self.assertEqual(worker.validate(),'verified_and_restored')
        self.assertEqual(self.uploads,1)

    def test_daily_cutoff_and_duplicate_prevention(self):
        self.live(); worker.validate()
        os.environ[host.FLAG]=host.FLAG_VALUE
        now=datetime.now(timezone.utc).replace(hour=6,minute=14)
        self.assertEqual(worker.due(now),'waiting')
        self.assertEqual(worker.due(now.replace(minute=15)),'verified_and_restored')
        self.assertEqual(worker.due(now.replace(hour=10)),'already_verified')
        self.assertEqual(self.uploads,2)  # Un ensayo y una copia diaria.

    def test_existing_railway_day_is_downloaded_and_not_duplicated(self):
        self.live(); name,_=self.generation(); original=self.objects[name]
        worker.validate(); os.environ[host.FLAG]=host.FLAG_VALUE
        now=datetime.now(timezone.utc).replace(hour=7)
        self.assertEqual(worker.due(now),'verified_and_restored')
        self.assertEqual(self.uploads,1)
        receipt=host.read_receipt('heraldo-test-'+now.strftime('%Y%m%d')+'.json')
        self.assertTrue(receipt['adopted_download_only'])
        self.assertEqual(self.objects[name],original)

    def test_scheduler_disabled_until_real_validation_receipt(self):
        self.live()
        with patch.object(scheduler._check_due,'start') as start:
            self.assertFalse(scheduler.start_if_authorized())
            os.environ[host.FLAG]=host.FLAG_VALUE
            with self.assertRaises(job.BackupJobError): scheduler.start_if_authorized()
        start.assert_not_called()

    def test_scheduler_does_not_duplicate_and_child_has_no_token(self):
        self.live(); worker.validate(); os.environ[host.FLAG]=host.FLAG_VALUE
        os.environ['DISCORD_TOKEN']='PRIVATE'
        with patch.object(scheduler._check_due,'is_running',side_effect=[False,True]),patch.object(scheduler._check_due,'start') as start,redirect_stdout(StringIO()):
            scheduler.start_if_authorized(); scheduler.start_if_authorized()
        self.assertEqual(start.call_count,1)
        with patch.object(scheduler.subprocess,'run',return_value=subprocess.CompletedProcess([],0,b'',b'')) as run:
            scheduler._invoke()
        self.assertIn('enzonic_test_backup',run.call_args.args[0])
        self.assertNotIn('DISCORD_TOKEN',run.call_args.kwargs['env'])

    def test_remote_budget_rejects_before_upload(self):
        self.live()
        with patch.object(worker,'REMOTE_BUDGET_BYTES',1):
            with self.assertRaisesRegex(job.BackupJobError,'remote_storage_budget_exhausted'):
                worker.validate()
        self.assertEqual(self.uploads,0)

    def test_low_disk_budget_leaves_live_database_intact(self):
        self.live(); before=self.db.read_bytes()
        with patch.object(host,'DISK_CAP_BYTES',1):
            with self.assertRaisesRegex(job.BackupJobError,'insufficient_backup_headroom'):
                worker.validate()
        self.assertEqual(self.db.read_bytes(),before); self.assertEqual(self.uploads,0)

    def test_foreign_key_corruption_blocks_backup(self):
        self.live()
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("INSERT INTO child VALUES(999,'invalid')"); db.commit()
        with self.assertRaisesRegex(recovery.RecoveryError,'foreign_keys_failed'):
            worker.validate()
        self.assertEqual(self.uploads,0)

    def test_validation_purpose_cannot_be_used_in_production(self):
        self.live()
        with patch.object(job,'_guard'):
            with self.assertRaises(job.BackupJobError):
                job.run_once(self.db,self.state,environment='heraldo-production',
                             revision='a'*40,purpose='validation',request_id=worker.VALIDATION_ID)
        self.assertEqual(self.uploads,0)

    def test_provider_output_not_forwarded_to_scheduler_log(self):
        scheduler._last_status=None
        out=StringIO()
        with patch.object(scheduler,'_invoke',side_effect=RuntimeError('PRIVATE')),redirect_stdout(out):
            asyncio.run(scheduler._check_due.coro())
        self.assertNotIn('PRIVATE',out.getvalue())


if __name__ == '__main__':
    unittest.main()
