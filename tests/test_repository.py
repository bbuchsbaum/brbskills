"""Exercise isolated downloads, synchronization, and refusal of unsafe paths."""
import contextlib
import hashlib
import importlib.util
import io
import tempfile
import unittest
import zipfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'skills.py'
spec = importlib.util.spec_from_file_location('skills', SCRIPT)
skills = importlib.util.module_from_spec(spec)
spec.loader.exec_module(skills)


class RepositoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'skills' / 'example'
        (self.source / 'references').mkdir(parents=True)
        (self.source / 'agents').mkdir()
        (self.source / 'SKILL.md').write_text(
            '---\nname: example\ndescription: Tests an isolated fixture.\n---\n'
            '# Example\nRead [detail](references/detail.md) when needed.\n')
        (self.source / 'references/detail.md').write_text('Fixture details.\n')
        (self.source / 'agents/openai.yaml').write_text('interface:\n  display_name: "Example"\n')
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)
        self.catalog = skills.sources(self.root)
        skills.sync(self.root, self.catalog)

    def test_both_products_share_workflow_and_references(self):
        for target in skills.TARGETS:
            self.assertEqual((self.root/target/'example/SKILL.md').read_bytes(),
                             (self.source/'SKILL.md').read_bytes())
            self.assertTrue((self.root/target/'example/references/detail.md').is_file())
        self.assertTrue((self.root/'codex/example/agents/openai.yaml').exists())
        self.assertFalse((self.root/'claude/example/agents/openai.yaml').exists())

    def test_drift_is_detected_and_repaired(self):
        (self.root/'claude/example/SKILL.md').write_text('Edited generated copy')
        with self.assertRaisesRegex(ValueError, 'Out of sync'):
            skills.check(self.root, self.catalog)
        skills.sync(self.root, self.catalog)
        skills.check(self.root, self.catalog)

    def test_removed_files_do_not_linger(self):
        (self.source/'extra.txt').write_text('temporary')
        skills.sync(self.root, self.catalog)
        (self.source/'extra.txt').unlink()
        skills.sync(self.root, self.catalog)
        self.assertFalse((self.root/'codex/example/extra.txt').exists())

    def test_unknown_output_is_not_silently_deleted(self):
        extra = self.root/'claude/unrecognized'
        extra.mkdir()
        with self.assertRaisesRegex(ValueError, 'obsolete'):
            skills.sync(self.root, self.catalog)
        self.assertTrue(extra.exists())

    def test_missing_and_added_generated_files_fail_check(self):
        (self.root/'codex/example/references/detail.md').unlink()
        (self.root/'claude/example/extra.txt').write_text('extra')
        with self.assertRaisesRegex(ValueError, 'Out of sync'):
            skills.check(self.root, self.catalog)

    def test_source_symlink_rejected(self):
        (self.source/'outside').symlink_to(self.root)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            skills.sources(self.root)

    def test_output_symlink_rejected_before_any_sync(self):
        (self.root/'claude/example/link').symlink_to(self.source/'SKILL.md')
        before = (self.root/'codex/example/SHA256SUMS').read_bytes()
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            skills.sync(self.root, self.catalog)
        self.assertEqual((self.root/'codex/example/SHA256SUMS').read_bytes(), before)

    def test_escaping_reference_rejected(self):
        with (self.source/'SKILL.md').open('a') as file:
            file.write('[outside](../../not-part-of-skill.md)\n')
        with self.assertRaisesRegex(ValueError, 'external local link'):
            skills.sources(self.root)

    def test_invalid_frontmatter_rejected(self):
        (self.source/'SKILL.md').write_text('---\nname: other\ndescription: okay\n---\nBody')
        with self.assertRaisesRegex(ValueError, 'name differ'):
            skills.sources(self.root)

    def test_package_is_deterministic_and_self_contained(self):
        skills.package(self.root, self.catalog, ['example'], 'both')
        before = {p.name: p.read_bytes() for p in (self.root/'dist').glob('*.zip')}
        skills.package(self.root, self.catalog, ['example'], 'both')
        self.assertEqual(before, {p.name: p.read_bytes() for p in (self.root/'dist').glob('*.zip')})
        for product in skills.TARGETS:
            with zipfile.ZipFile(self.root/'dist'/f'example-{product}.zip') as archive:
                self.assertTrue(all(n.startswith('example/') for n in archive.namelist()))
                checksums = archive.read('example/SHA256SUMS').decode().splitlines()
                self.assertEqual(len(checksums), len(archive.namelist()) - 1)
                for line in checksums:
                    digest, name = line.split('  ', 1)
                    self.assertEqual(hashlib.sha256(archive.read('example/'+name)).hexdigest(), digest)
                archive.extractall(self.root/f'extracted-{product}')
            skills.validate(self.root/f'extracted-{product}/example')

    def test_package_refuses_unknown_skill_or_stale_tree(self):
        with self.assertRaisesRegex(ValueError, 'Unknown skills'):
            skills.package(self.root, self.catalog, ['../outside'], 'both')
        (self.root/'claude/example/SHA256SUMS').write_text('stale')
        with self.assertRaisesRegex(ValueError, 'Out of sync'):
            skills.package(self.root, self.catalog, ['example'], 'both')

    def test_single_skill_and_product_package_excludes_other_skills(self):
        second = self.root/'skills/second'
        second.mkdir()
        (second/'SKILL.md').write_text('---\nname: second\ndescription: Second fixture.\n---\nBody\n')
        catalog = skills.sources(self.root)
        skills.sync(self.root, catalog)
        skills.package(self.root, catalog, ['example'], 'claude')
        self.assertEqual([p.name for p in (self.root/'dist').iterdir()], ['example-claude.zip'])

    def collection(self, name='member'):
        collection = self.root/'collections/workbench'
        member = collection/'skills'/name
        member.mkdir(parents=True)
        (member/'SKILL.md').write_text(
            f'---\nname: {name}\ndescription: Tests a collection member.\n'
            'license: MIT\ncompatibility: Python 3.10+\n'
            'metadata:\n  version: "0.1.0"\n---\n# Member\n')
        (collection/'shared/scripts').mkdir(parents=True)
        (collection/'shared/scripts/helper.py').write_text('print("shared")\n')
        (collection/'LICENSE').write_text('Fixture license\n')
        return collection, member

    def test_collection_skill_packages_independently_with_license_and_metadata(self):
        collection, member = self.collection()
        catalog = skills.sources(self.root, refresh_shared=True)
        skills.sync(self.root, catalog)
        skills.package(self.root, catalog, ['member'], 'both')
        for product in skills.TARGETS:
            with zipfile.ZipFile(self.root/'dist'/f'member-{product}.zip') as archive:
                self.assertEqual(archive.read('member/SKILL.md'), (member/'SKILL.md').read_bytes())
                self.assertEqual(archive.read('member/LICENSE'), (collection/'LICENSE').read_bytes())
                self.assertIn('member/scripts/helper.py', archive.namelist())
                self.assertTrue(all(n.startswith('member/') for n in archive.namelist()))

    def test_shared_source_drift_blocks_check_then_sync_refreshes_both_targets(self):
        collection, member = self.collection()
        catalog = skills.sources(self.root, refresh_shared=True)
        skills.sync(self.root, catalog)
        helper = collection/'shared/scripts/helper.py'
        helper.write_text('print("updated")\n')
        with self.assertRaisesRegex(ValueError, 'Shared resource out of sync'):
            skills.sources(self.root)
        catalog = skills.sources(self.root, refresh_shared=True)
        skills.sync(self.root, catalog)
        for product in skills.TARGETS:
            self.assertEqual((self.root/product/'member/scripts/helper.py').read_bytes(), helper.read_bytes())

    def test_duplicate_skill_name_across_collections_rejected(self):
        self.collection('example')
        with self.assertRaisesRegex(ValueError, 'Duplicate skill name'):
            skills.sources(self.root, refresh_shared=True)

    def test_collection_symlink_is_rejected(self):
        (self.root/'collections').mkdir()
        (self.root/'collections/linked').symlink_to(self.source)
        with self.assertRaisesRegex(ValueError, 'must not be a symlink'):
            skills.sources(self.root)

    def test_shared_refresh_refuses_destination_symlink(self):
        collection, member = self.collection()
        (member/'scripts').symlink_to(collection/'shared/scripts')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            skills.sources(self.root, refresh_shared=True)

    def test_optional_frontmatter_values_are_validated(self):
        for field in ('metadata: []', 'metadata:\n  version: 1', 'license: true',
                      'compatibility: false', 'allowed-tools: []', 'context: fork'):
            with self.subTest(field=field):
                (self.source/'SKILL.md').write_text(
                    '---\nname: example\ndescription: Fixture.\n'+field+'\n---\nBody\n')
                with self.assertRaises(ValueError):
                    skills.sources(self.root)


if __name__ == '__main__':
    unittest.main()
