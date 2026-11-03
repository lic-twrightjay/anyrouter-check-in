#!/usr/bin/env python3
"""Validate GitHub Actions account Secrets and inject individual accounts safely.

Never prints Secret values, cookies, access tokens, or the full Secrets map.
"""

import json
import os
import sys
from pathlib import Path

PREFIX = 'ANYROUTER_ACCOUNT_'


def prepare_accounts(secrets_map: dict, github_env: Path) -> tuple[int, int]:
	"""Return (base_count, individual_count), raising ValueError on bad setup."""
	if not isinstance(secrets_map, dict):
		raise ValueError('GitHub Secrets context is not a JSON object')

	base_raw = secrets_map.get('ANYROUTER_ACCOUNTS') or '[]'
	try:
		base_accounts = json.loads(base_raw)
	except (TypeError, json.JSONDecodeError) as exc:
		raise ValueError('ANYROUTER_ACCOUNTS must contain a JSON array') from exc
	if not isinstance(base_accounts, list):
		raise ValueError('ANYROUTER_ACCOUNTS must contain a JSON array, such as []')

	individual_accounts = {}
	for name, raw in sorted(secrets_map.items()):
		if not name.startswith(PREFIX) or name == 'ANYROUTER_ACCOUNTS':
			continue
		try:
			account = json.loads(raw)
		except (TypeError, json.JSONDecodeError) as exc:
			raise ValueError(f'{name} must contain a JSON object') from exc
		if not isinstance(account, dict):
			raise ValueError(f'{name} must contain a JSON object')
		if not account.get('cookies') and not account.get('access_token'):
			raise ValueError(f'{name} is missing cookies or access_token')
		# Compact JSON ensures even multi-line Secrets can be written to GITHUB_ENV
		# without injecting unintended environment-variable entries.
		individual_accounts[name] = json.dumps(account, ensure_ascii=True, separators=(',', ':'))

	if not base_accounts and not individual_accounts:
		raise ValueError(
			'No accounts available: ANYROUTER_ACCOUNTS is empty and no '
			'ANYROUTER_ACCOUNT_* Secrets are visible. Check the extension GitHub '
			'repository and Environment (production), then use Sync All. '
			'Test Account does not upload Secrets.'
		)

	with github_env.open('a', encoding='utf-8') as env_file:
		for name, compact_value in individual_accounts.items():
			env_file.write(f'{name}={compact_value}\n')

	return len(base_accounts), len(individual_accounts)


def main() -> int:
	try:
		secrets_map = json.loads(os.getenv('ALL_SECRETS', '{}'))
		github_env = os.environ.get('GITHUB_ENV')
		if not github_env:
			raise ValueError('GITHUB_ENV is unavailable')
		base_count, individual_count = prepare_accounts(secrets_map, Path(github_env))
	except (ValueError, OSError, json.JSONDecodeError) as exc:
		print(f'::error title=Account Secrets configuration::{exc}', file=sys.stderr)
		return 1

	print(f'[INFO] GitHub account Secrets ready: {base_count} base, {individual_count} individual')
	return 0


if __name__ == '__main__':
	sys.exit(main())
