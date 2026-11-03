import pytest

import checkin
from checkin import NON_RETRYABLE_USER_INFO_ERRORS, _parse_browser_user_info
from utils.config import AccountConfig, AppConfig, ProviderConfig


@pytest.mark.parametrize(
    ('response', 'error_type', 'expected_message'),
    [
        ({'_fetch_error_type': 'cloudflare_challenge', '_http_status': 200}, 'cloudflare_challenge', 'Cloudflare verification HTML'),
        ({'_fetch_error_type': 'login_page', '_http_status': 200}, 'login_page', 'Login page'),
        ({'_fetch_error_type': 'unexpected_html', '_http_status': 200}, 'unexpected_html', 'HTML returned instead'),
        ({'_fetch_error_type': 'invalid_json', '_http_status': 200}, 'invalid_json_permanent', 'not valid JSON'),
        ({'_fetch_error_type': 'http_error', '_http_status': 403}, 'http_access_denied', 'HTTP 403'),
        ({'_fetch_error_type': 'http_error', '_http_status': 404}, 'http_not_found', 'HTTP 404'),
    ],
)
def test_permanent_non_json_or_access_failure_is_actionable(response, error_type, expected_message):
    parsed = _parse_browser_user_info({'success': False, **response})
    assert parsed['success'] is False
    assert parsed['error_type'] == error_type
    assert error_type in NON_RETRYABLE_USER_INFO_ERRORS
    assert expected_message in parsed['error']


def test_successful_user_info_retains_balance():
    parsed = _parse_browser_user_info({'success': True, 'data': {'quota': 500000, 'used_quota': 250000}})
    assert parsed['success'] is True
    assert parsed['quota'] == 1
    assert parsed['used_quota'] == 0.5


def test_retryable_network_error_is_classified_without_secret_leak():
    parsed = _parse_browser_user_info({'success': False, '_fetch_error_type': 'network_error'})
    assert parsed['error_type'] == 'network_error'
    assert parsed['error_type'] not in NON_RETRYABLE_USER_INFO_ERRORS
    assert 'network request failed' in parsed['error']


@pytest.mark.parametrize(
    ('response', 'expected_type'),
    [
        ({'_fetch_error_type': 'request_timeout'}, 'request_timeout'),
        ({'_fetch_error_type': 'http_error', '_http_status': 502}, 'http_error'),
        ({'_fetch_error_type': 'invalid_json', '_http_status': 503}, 'invalid_json'),
    ],
)
def test_transient_failures_remain_retryable(response, expected_type):
    parsed = _parse_browser_user_info({'success': False, **response})
    assert parsed['error_type'] == expected_type
    assert expected_type not in NON_RETRYABLE_USER_INFO_ERRORS


def test_invalid_body_type_is_safe():
    parsed = _parse_browser_user_info('<html>secret</html>')
    assert parsed['success'] is False
    assert '<html>' not in parsed['error']


@pytest.mark.asyncio
@pytest.mark.parametrize('manual_check_in', [False, True])
@pytest.mark.parametrize(
    ('fetch_kind', 'status', 'expected_kind'),
    [
        ('cloudflare_challenge', 200, 'cloudflare_challenge'),
        ('login_page', 200, 'login_page'),
        ('unexpected_html', 200, 'unexpected_html'),
        ('invalid_json', 200, 'invalid_json_permanent'),
        ('http_error', 403, 'http_access_denied'),
    ],
)
async def test_blocked_browser_page_never_submits_checkin(monkeypatch, manual_check_in, fetch_kind, status, expected_kind):
    class FakePage:
        def set_default_timeout(self, *args): pass
        async def goto(self, *args, **kwargs): pass
        async def wait_for_load_state(self, *args, **kwargs): pass
        async def wait_for_function(self, *args, **kwargs): pass

    class FakeContext:
        def __init__(self):
            self.closed = False
        async def add_init_script(self, *args): pass
        async def add_cookies(self, *args): pass
        async def new_page(self): return FakePage()
        async def close(self): self.closed = True

    class FakeChromium:
        async def launch_persistent_context(self, **kwargs): return context

    class FakePW:
        chromium = FakeChromium()

    class FakePlaywright:
        async def __aenter__(self): return FakePW()
        async def __aexit__(self, *args): return False

    context = FakeContext()
    requests = []
    async def fake_eval(page, script, args):
        requests.append(script)
        return {'success': False, '_fetch_error_type': fetch_kind, '_http_status': status}

    monkeypatch.setattr(checkin, 'async_playwright', lambda: FakePlaywright())
    monkeypatch.setattr(checkin, 'safe_page_eval', fake_eval)
    provider = ProviderConfig(
        name='agentrouter',
        domain='https://agentrouter.org',
        sign_in_path='/api/user/sign_in' if manual_check_in else None,
    )
    account = AccountConfig(cookies={'session': 'test-session'}, api_user='356997', provider='agentrouter')
    success, before, after = await checkin.check_in_with_playwright(account, 'Account 1', provider)
    assert not success
    assert before['error_type'] == expected_kind
    assert after is None
    assert len(requests) == 1  # no POST or extra GET after a rejected page
    assert context.closed


@pytest.mark.asyncio
async def test_browser_transient_network_error_recovers_before_checkin(monkeypatch):
    class FakePage:
        def __init__(self):
            self.waits = []
        def set_default_timeout(self, *args): pass
        async def goto(self, *args, **kwargs): pass
        async def wait_for_load_state(self, *args, **kwargs): pass
        async def wait_for_function(self, *args, **kwargs): pass
        async def wait_for_timeout(self, delay):
            self.waits.append(delay)

    class FakeContext:
        def __init__(self):
            self.closed = False
        async def add_init_script(self, *args): pass
        async def add_cookies(self, *args): pass
        async def new_page(self): return page
        async def close(self): self.closed = True

    class FakePlaywright:
        async def __aenter__(self): return type('PW', (), {'chromium': self})()
        async def __aexit__(self, *args): return False
        async def launch_persistent_context(self, **kwargs): return context

    page = FakePage()
    context = FakeContext()
    calls = []

    async def fake_eval(page_obj, script, args):
        calls.append(args)
        if len(calls) == 1:
            return {'success': False, '_fetch_error_type': 'network_error'}
        return {'success': True, 'data': {'quota': 500000, 'used_quota': 0}}

    monkeypatch.setattr(checkin, 'async_playwright', lambda: FakePlaywright())
    monkeypatch.setattr(checkin, 'safe_page_eval', fake_eval)
    provider = ProviderConfig(name='agentrouter', domain='https://agentrouter.org', sign_in_path=None)
    account = AccountConfig(cookies={'session': 'test-session'}, api_user='356997', provider='agentrouter')
    success, before, after = await checkin.check_in_with_playwright(account, 'Account 1', provider)
    assert success is True
    assert before['quota'] == 1
    assert after['success'] is True
    assert len(calls) == 3  # first GET failed, retry GET succeeded, post-check GET succeeded
    assert checkin.RETRY_DELAY * 1000 in page.waits
    assert context.closed


@pytest.mark.asyncio
async def test_main_skips_second_pass_for_cloudflare_html(monkeypatch, capsys):
    account = AccountConfig(
        cookies={'session': 'test-session'},
        api_user='356997',
        provider='agentrouter',
    )
    provider = ProviderConfig(
        name='agentrouter', domain='https://agentrouter.org', sign_in_path=None
    )
    monkeypatch.setattr(checkin.AppConfig, 'load_from_env', lambda: AppConfig(providers={'agentrouter': provider}))
    monkeypatch.setattr(checkin, 'load_accounts_config', lambda: [account])
    monkeypatch.setattr(checkin, 'load_balance_hash', lambda: None)
    monkeypatch.setattr(checkin.notify, 'push_message', lambda *args, **kwargs: None)
    calls = []

    async def fake_check_in_account(*args):
        calls.append(True)
        info = _parse_browser_user_info({
            'success': False,
            '_fetch_error_type': 'cloudflare_challenge',
            '_http_status': 200,
        })
        return False, info, None

    async def forbid_sleep(*args):
        raise AssertionError('Cloudflare HTML failure should not enter retry cooldown')

    monkeypatch.setattr(checkin, 'check_in_account', fake_check_in_account)
    monkeypatch.setattr(checkin.asyncio, 'sleep', forbid_sleep)
    with pytest.raises(SystemExit) as exit_info:
        await checkin.main()
    assert exit_info.value.code == 1
    assert len(calls) == 1
    output = capsys.readouterr().out
    assert 'Skipping automatic retry for 1 account(s)' in output
    assert 'Cloudflare verification HTML' in output


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'kind',
    ['cloudflare_challenge', 'login_page', 'unexpected_html', 'invalid_json'],
)
async def test_main_rejects_permanent_response_without_second_pass(monkeypatch, kind):
    account = AccountConfig(cookies={'session': 'test-session'}, api_user='356997', provider='agentrouter')
    provider = ProviderConfig(name='agentrouter', domain='https://agentrouter.org', sign_in_path=None)
    monkeypatch.setattr(checkin.AppConfig, 'load_from_env', lambda: AppConfig(providers={'agentrouter': provider}))
    monkeypatch.setattr(checkin, 'load_accounts_config', lambda: [account])
    monkeypatch.setattr(checkin, 'load_balance_hash', lambda: None)
    monkeypatch.setattr(checkin.notify, 'push_message', lambda *args, **kwargs: None)
    calls = []

    async def failed_check_in(*args):
        calls.append(True)
        return False, _parse_browser_user_info({
            'success': False, '_fetch_error_type': kind, '_http_status': 200
        }), None

    async def disallow_sleep(delay):
        raise AssertionError('A permanent response must skip the second pass')

    monkeypatch.setattr(checkin, 'check_in_account', failed_check_in)
    monkeypatch.setattr(checkin.asyncio, 'sleep', disallow_sleep)
    with pytest.raises(SystemExit) as exit_info:
        await checkin.main()
    assert exit_info.value.code == 1
    assert calls == [True]


@pytest.mark.asyncio
async def test_main_retries_network_error_once_and_records_recovery(monkeypatch, capsys):
    account = AccountConfig(cookies={'session': 'test-session'}, api_user='356997', provider='agentrouter')
    provider = ProviderConfig(name='agentrouter', domain='https://agentrouter.org', sign_in_path=None)
    monkeypatch.setattr(checkin.AppConfig, 'load_from_env', lambda: AppConfig(providers={'agentrouter': provider}))
    monkeypatch.setattr(checkin, 'load_accounts_config', lambda: [account])
    monkeypatch.setattr(checkin, 'load_balance_hash', lambda: None)
    monkeypatch.setattr(checkin, 'save_balance_hash', lambda hash_value: None)
    monkeypatch.setattr(checkin.notify, 'push_message', lambda *args, **kwargs: None)
    calls, sleeps = [], []

    async def fake_check_in_account(*args):
        calls.append(True)
        if len(calls) == 1:
            return False, _parse_browser_user_info(
                {'success': False, '_fetch_error_type': 'network_error'}
            ), None
        info = {'success': True, 'quota': 1.0, 'used_quota': 0.0}
        return True, info, info

    async def record_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(checkin, 'check_in_account', fake_check_in_account)
    monkeypatch.setattr(checkin.asyncio, 'sleep', record_sleep)
    with pytest.raises(SystemExit) as exit_info:
        await checkin.main()
    assert exit_info.value.code == 0
    assert len(calls) == 2
    assert len(sleeps) == 1
    assert 60 <= sleeps[0] <= 120
    assert 'succeeded on retry' in capsys.readouterr().out
