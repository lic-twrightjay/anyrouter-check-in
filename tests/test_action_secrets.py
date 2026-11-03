"""Regression checks for GitHub Actions account Secret preflight."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.prepare_action_accounts import prepare_accounts


def test_accepts_base_accounts_with_no_individual_secrets(tmp_path):
	github_env = tmp_path / 'github_env'
	accounts = [{'cookies': {'session': 'test-session'}, 'api_user': '123'}]
	assert prepare_accounts({'ANYROUTER_ACCOUNTS': json.dumps(accounts)}, github_env) == (1, 0)
	assert github_env.read_text(encoding='utf-8') == ''


def test_accepts_multiline_individual_secret_when_base_is_empty(tmp_path):
	github_env = tmp_path / 'github_env'
	account = {'cookies': {'session': 'test-session'}, 'api_user': '123', 'provider': 'anyrouter'}
	key = 'ANYROUTER_ACCOUNT_123_ANYROUTER'
	assert prepare_accounts({'ANYROUTER_ACCOUNTS': '[]', key: json.dumps(account, indent=2)}, github_env) == (0, 1)
	name, value = github_env.read_text(encoding='utf-8').strip().split('=', 1)
	assert name == key
	assert json.loads(value) == account
	assert '\n' not in value


def test_rejects_empty_base_and_missing_individual_accounts(tmp_path):
	with pytest.raises(ValueError, match='No accounts available'):
		prepare_accounts({'ANYROUTER_ACCOUNTS': '[]'}, tmp_path / 'github_env')


def test_rejects_invalid_individual_secret(tmp_path):
	with pytest.raises(ValueError, match='must contain a JSON object'):
		prepare_accounts({'ANYROUTER_ACCOUNT_123_ANYROUTER': '[123]'}, tmp_path / 'github_env')


def test_rejects_account_without_authentication(tmp_path):
	with pytest.raises(ValueError, match='missing cookies or access_token'):
		prepare_accounts({'ANYROUTER_ACCOUNT_123_ANYROUTER': '{"api_user":"123"}'}, tmp_path / 'github_env')


def test_accepts_access_token_individual_secret(tmp_path):
	github_env = tmp_path / 'github_env'
	key = 'ANYROUTER_ACCOUNT_123_ANYROUTER'
	assert prepare_accounts({key: '{"access_token":"test-token","api_user":"123"}'}, github_env) == (0, 1)
	assert key in github_env.read_text(encoding='utf-8')
