"""Carl-style embeds preserve the existing global footer, never define their own."""
import unittest
from types import SimpleNamespace as NS

import discord
import autofeed_embed_builder as builder
import autofeed_setup as setup
from test_safety_regressions import b


class EmbedBuilderTests(unittest.TestCase):
    def test_full_discord_embed_stamped_with_existing_lab_footer(self):
        data = {
            "title": "Aviso", "description": "Revisa <#123456789012345678>",
            "url": "https://example.org/novedades", "color_hex": "2F94C0",
            "author": {"name": "El Heraldo", "url": "https://example.org",
                       "icon_url": "https://example.org/avatar.png"},
            "image_url": "https://example.org/image.png",
            "thumbnail_url": "https://example.org/thumb.png",
            "fields": [{"name": "Horario", "value": "Viernes", "inline": True},
                       {"name": "Canal", "value": "<#123456789012345678>", "inline": False}],
            "timestamp": True,
            "footer": {"text": "NO PUEDE REEMPLAZAR EL FOOTER"},
        }
        observed = []
        def stamp(embed, guild):
            observed.append(guild.id)
            embed.set_footer(text="El Heraldo's Labs 🧪")
            return embed
        visual = builder.render(data, stamp, NS(id=901))
        self.assertEqual(observed, [901])
        self.assertEqual(visual.footer.text, "El Heraldo's Labs 🧪")
        self.assertEqual(visual.title, "Aviso")
        self.assertEqual(visual.description, "Revisa <#123456789012345678>")
        self.assertEqual(visual.url, "https://example.org/novedades")
        self.assertEqual(visual.author.name, "El Heraldo")
        self.assertEqual(visual.author.icon_url, "https://example.org/avatar.png")
        self.assertEqual(visual.image.url, "https://example.org/image.png")
        self.assertEqual(visual.thumbnail.url, "https://example.org/thumb.png")
        self.assertEqual(len(visual.fields), 2)
        self.assertEqual(visual.fields[0].inline, True)
        self.assertIsNotNone(visual.timestamp)

    def test_footer_is_not_an_editable_section(self):
        parent = setup.AutofeedEditorView(b.__dict__, 901, 10)
        view = builder.EmbedBuilderView(parent)
        sections = [option.value for option in view.section_select.options]
        self.assertEqual(sections, ["main", "author", "media", "fields", "date"])
        self.assertNotIn("footer", sections)
        self.assertIn(builder.t("locked"), view.summary())
        self.assertEqual(parent.embed, None)
        self.assertFalse(parent.dirty)

    def test_validates_urls_fields_and_length(self):
        for key, value in (
            ("url", "http://example.org"),
            ("image_url", "javascript:alert(1)"),
            ("thumbnail_url", "ftp://example.org/thumb.png"),
        ):
            with self.subTest(key=key), self.assertRaises(ValueError):
                builder.validate_data({"description": "texto", key: value})
        with self.assertRaises(ValueError):
            builder.validate_data({
                "description": "ok",
                "fields": [{"name": str(i), "value": "value"} for i in range(26)],
            })
        self.assertEqual(builder.validate_data({"description": "Contenido"})["fields"], [])
        self.assertFalse(builder.has_content({"color_hex": "FFFFFF", "timestamp": True}))

    def test_form_modal_separates_author_images_and_content(self):
        parent = setup.AutofeedEditorView(b.__dict__, 901, 10)
        for section, count in (("main", 3), ("author", 3), ("media", 2)):
            with self.subTest(section=section):
                self.assertEqual(len(builder.SectionModal(parent, section).children), count)
        self.assertEqual(len(builder.FieldModal(parent).children), 3)
        main = builder.SectionModal(parent, "main")
        self.assertNotIn("url", main.inputs)
        self.assertIn("Guardar", main.title)

    def test_parent_editor_uses_new_builder_and_persists_only_on_confirmation(self):
        parent = setup.AutofeedEditorView(b.__dict__, 901, 10)
        pre = b.guild_config_get(901, "message_schedules")
        builder.update(parent, {"description": "Hola", "timestamp": True})
        self.assertTrue(parent.dirty)
        self.assertEqual(pre, b.guild_config_get(901, "message_schedules"))


if __name__ == "__main__":
    unittest.main()
