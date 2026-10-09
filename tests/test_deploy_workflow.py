"""Exercise workflow shell bodies without SSH, Docker, Railway, or live APIs."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = yaml.load((ROOT / '.github/workflows/deploy.yml').read_text(), Loader=yaml.BaseLoader)
STEPS = WORKFLOW['jobs']['build-and-deploy']['steps']


def step(name):
    return next(item for item in STEPS if item.get('name') == name)


class DeployWorkflowTests(unittest.TestCase):
    def preflight(self, target='none', ref='refs/heads/main', oracle='false', railway='false'):
        env = dict(os.environ, DEPLOY_TARGET=target, DEPLOY_REF=ref,
                   HAS_ORACLE_CONFIG=oracle, HAS_RAILWAY_TOKEN=railway)
        return subprocess.run(['bash', '-c', step('Validate deployment request')['run']],
                              env=env, capture_output=True, text=True)

    def test_push_build_requires_no_credentials(self):
        for ref in ['refs/heads/main', 'refs/heads/master']:
            self.assertEqual(self.preflight(ref=ref).returncode, 0)

    def test_manual_build_on_default_branch_requires_no_credentials(self):
        self.assertEqual(self.preflight(ref='refs/heads/secure-key-setup').returncode, 0)

    def test_deploy_rejects_other_branches_and_tags(self):
        for target in ['oracle', 'railway']:
            for ref in ['refs/heads/secure-key-setup', 'refs/heads/feature', 'refs/tags/main']:
                self.assertNotEqual(self.preflight(target, ref, 'true', 'true').returncode, 0)

    def test_selected_target_requires_its_own_credentials(self):
        self.assertNotEqual(self.preflight('oracle', railway='true').returncode, 0)
        self.assertNotEqual(self.preflight('railway', oracle='true').returncode, 0)

    def test_configured_targets_are_accepted(self):
        self.assertEqual(self.preflight('oracle', oracle='true').returncode, 0)
        self.assertEqual(self.preflight('railway', railway='true').returncode, 0)

    def test_unknown_target_is_rejected(self):
        self.assertNotEqual(self.preflight('both', oracle='true', railway='true').returncode, 0)

    def test_every_shell_body_parses(self):
        for item in STEPS:
            if 'run' in item:
                result = subprocess.run(['bash', '-n'], input=item['run'], text=True,
                                        capture_output=True)
                self.assertEqual(result.returncode, 0, (item['name'], result.stderr))

    def test_summary_distinguishes_skipped_deployment(self):
        with tempfile.TemporaryDirectory() as directory:
            summary = Path(directory) / 'summary'
            for oracle, railway, expected in [('skipped', 'skipped', 'No deployment'),
                                              ('success', 'skipped', 'live health is not verified'),
                                              ('skipped', 'success', 'live health is not verified')]:
                summary.write_text('')
                env = dict(os.environ, GITHUB_STEP_SUMMARY=str(summary),
                           ORACLE_OUTCOME=oracle, RAILWAY_OUTCOME=railway, DEPLOY_TARGET='oracle')
                result = subprocess.run(['bash', '-c', step('Report result')['run']], env=env)
                self.assertEqual(result.returncode, 0)
                self.assertIn(expected, summary.read_text())

    def remote(self, merge_status=0, actual_sha='abc', build_status=0):
        # Test mode: all remote commands are shell stubs, never live integrations.
        script = step('Deploy to Oracle Cloud')['run'].split("<<'EOF'\n", 1)[1].rsplit('\nEOF', 1)[0]
        stubs = '''
        cd() { return 0; }
        git() {
          echo "git $*" >&2
          case "$1" in
            merge) return "$MERGE_STATUS" ;;
            rev-parse) echo "$ACTUAL_SHA" ;;
          esac
        }
        docker() {
          echo "docker $*" >&2
          if [[ "$*" == 'compose build' ]]; then return "$BUILD_STATUS"; fi
          return 0
        }
        '''
        env = dict(os.environ, MERGE_STATUS=str(merge_status), ACTUAL_SHA=actual_sha,
                   BUILD_STATUS=str(build_status))
        return subprocess.run(['bash', '-c', stubs + script, 'test', 'abc'], env=env,
                              capture_output=True, text=True)

    def test_remote_merge_failure_never_starts_containers(self):
        result = self.remote(merge_status=1)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('docker compose up', result.stderr)

    def test_remote_wrong_revision_never_starts_containers(self):
        result = self.remote(actual_sha='other')
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('docker compose up', result.stderr)

    def test_remote_build_failure_never_starts_containers(self):
        result = self.remote(build_status=1)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn('docker compose up', result.stderr)

    def test_remote_exact_revision_builds_then_starts_without_pruning(self):
        result = self.remote()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('git merge --ff-only abc', result.stderr)
        self.assertIn('docker compose up -d', result.stderr)
        self.assertNotIn('prune', result.stderr)
        self.assertNotIn('compose down', result.stderr)


if __name__ == '__main__':
    unittest.main()
