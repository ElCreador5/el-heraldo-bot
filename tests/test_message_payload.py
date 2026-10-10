import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from message_payload import validate, render, import_kit


class MessagePayloadTests(unittest.TestCase):
    def test_plain_content_and_variables(self):
        content, embeds = render({'content': 'Hola {usuario} en {servidor}'}, {'usuario': 'Ana', 'servidor': 'Lab'})
        self.assertEqual(content, 'Hola Ana en Lab')
        self.assertEqual(embeds, [])

    def test_legacy_embed_still_renders(self):
        content, embeds = render({'title': 'Título', 'description': 'Texto', 'image': 'https://example.org/a.png'})
        self.assertIsNone(content)
        self.assertEqual(embeds[0]['image']['url'], 'https://example.org/a.png')

    def test_rich_multi_embed(self):
        payload = {'content': 'Texto', 'embeds': [
            {'title': 'Uno', 'thumbnail': {'url': 'https://example.org/a.png'},
             'author': {'name': 'Autor'}, 'footer': {'text': 'Pie'},
             'fields': [{'name': 'Campo', 'value': 'Valor', 'inline': True}]}, {'description': 'Dos'}]}
        self.assertEqual(render(payload)[1], payload['embeds'])

    def test_limits_and_types(self):
        invalid = [{'content': 'a' * 2001}, {'embeds': [{'description': 'a' * 3500}] * 2},
                   {'embeds': [{'title': 'x', 'color': True}]}, {'embeds': [{'title': 'x'}] * 11},
                   {'image': 'javascript:alert(1)'}, {'title': 'x', 'button_url': 'https://example.org'},
                   {'title': 'x', 'unknown': 'no'}, {'embeds': [{}]},
                   {'embeds': [{'image': {'url': ''}}]}, {'embeds': [{'author': {'icon_url': 'https://example.org/a.png'}}]}]
        for payload in invalid:
            with self.subTest(payload=str(payload)[:70]), self.assertRaises(ValueError):
                validate(payload)

    def test_variable_expansion_is_revalidated(self):
        with self.assertRaises(ValueError):
            render({'content': '{usuario}' * 200}, {'usuario': 'x' * 32})

    def test_kit_strips_actions_and_preserves_visuals(self):
        result = import_kit({'version': 2, 'templates': [{'name': 'Uno', 'content': 'Hola',
            'embeds': [{'title': 'Título'}], 'role_component': 'Administrador', 'actions': ['danger']}]})
        self.assertEqual(result[0]['role_component'], '')
        self.assertNotIn('actions', result[0])
        self.assertEqual(result[0]['embeds'][0]['title'], 'Título')

    def test_kit_duplicate_names_rejected(self):
        with self.assertRaises(ValueError):
            import_kit({'version': 2, 'templates': [{'name': 'A', 'content': 'x'}, {'name': 'a', 'content': 'x'}]})


if __name__ == '__main__':
    unittest.main()
