import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import issue23_production_config as config


class TemporaryConfigTests(unittest.TestCase):
    def test_install_adds_only_backup_variables_without_deploy_or_replacement(self):
        update = config.prepare_update({key: 'synthetic' for key in config.TEMPORARY})
        self.assertFalse(update['replace'])
        self.assertTrue(update['skipDeploys'])
        self.assertFalse(config.ORIGINAL & set(update['variables']))
        self.assertNotIn('HERALDO_PRODUCTION_BACKUP_ENABLED', update['variables'])

    def test_cleanup_restores_only_original_configuration_without_deploy(self):
        update = config.prepare_update({key: 'synthetic' for key in config.ORIGINAL}, cleanup=True)
        self.assertTrue(update['replace'])
        self.assertTrue(update['skipDeploys'])
        self.assertEqual(set(update['variables']), config.ORIGINAL)

    def test_partial_unexpected_or_empty_values_are_rejected(self):
        for values in ({}, {'DISCORD_TOKEN': 'synthetic'},
                       {key: '' for key in config.TEMPORARY},
                       {**{key: 'synthetic' for key in config.TEMPORARY}, 'OTHER': 'synthetic'}):
            with self.assertRaises(RuntimeError):
                config.prepare_update(values)

    def test_platform_variables_are_never_written_as_custom_variables(self):
        self.assertEqual(config.explicit_variables({'RAILWAY_PROJECT_ID': 'synthetic',
                                                    'DB_PATH': '/synthetic'}),
                         {'DB_PATH': '/synthetic'})


if __name__ == '__main__':
    unittest.main()
