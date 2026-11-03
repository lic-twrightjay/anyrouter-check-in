// Evaluated inside the active Playwright page. Never return raw HTML, cookies,
// request headers, or tokens to the Python logs.
async ([path, headerName, userId, token]) => {
  try {
    const headers = { Accept: 'application/json' };
    if (headerName && userId) headers[headerName] = userId;
    if (token) headers.Authorization = token;
    const response = await fetch(path, {
      headers,
      credentials: 'same-origin',
      signal: AbortSignal.timeout(15000)
    });
    const contentType = (response.headers.get('content-type') || '').split(';')[0].toLowerCase();
    const body = await response.text();
    let data;
    try {
      data = JSON.parse(body);
    } catch {
      const snippet = body.slice(0, 8192).toLowerCase();
      const html = /<!doctype\s+html|<html\b|text\/html/.test(snippet + ' ' + contentType);
      const cloudflare = html && (
        snippet.includes('cloudflare') ||
        snippet.includes('cf-chl') ||
        snippet.includes('challenge-platform') ||
        snippet.includes('just a moment') ||
        snippet.includes('verify you are human') ||
        snippet.includes('attention required')
      );
      const login = html && /\/(?:login|signin|sign-in)(?:[/?#]|$)/i.test(response.url || '');
      return {
        success: false,
        _fetch_error_type: cloudflare ? 'cloudflare_challenge' :
          login ? 'login_page' : html ? 'unexpected_html' : 'invalid_json',
        _http_status: response.status,
        _content_type: contentType || 'unknown'
      };
    }
    if (!response.ok) {
      return { success: false, _fetch_error_type: 'http_error', _http_status: response.status };
    }
    if (!data || typeof data !== 'object' || Array.isArray(data)) {
      return { success: false, _fetch_error_type: 'invalid_json', _http_status: response.status };
    }
    return data;
  } catch (error) {
    return {
      success: false,
      _fetch_error_type: error?.name === 'TimeoutError' || error?.name === 'AbortError'
        ? 'request_timeout' : 'network_error'
    };
  }
}
