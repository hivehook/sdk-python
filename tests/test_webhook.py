import time

from hivehook.webhook import sign, verify, verify_with_rotation, generate_secret


def test_sign_and_verify():
    secret = generate_secret()
    payload = '{"event": "test"}'
    sig, ts = sign(payload, secret)
    assert verify(payload, secret, sig, ts)


def test_verify_wrong_secret():
    secret = generate_secret()
    other = generate_secret()
    payload = '{"event": "test"}'
    sig, ts = sign(payload, secret)
    assert not verify(payload, other, sig, ts)


def test_verify_wrong_payload():
    secret = generate_secret()
    sig, ts = sign("original", secret)
    assert not verify("tampered", secret, sig, ts)


def test_verify_expired_timestamp():
    secret = generate_secret()
    payload = "test"
    old_ts = int(time.time()) - 600
    sig, _ = sign(payload, secret, old_ts)
    assert not verify(payload, secret, sig, old_ts, tolerance=300)


def test_verify_no_tolerance():
    secret = generate_secret()
    payload = "test"
    old_ts = int(time.time()) - 99999
    sig, _ = sign(payload, secret, old_ts)
    assert verify(payload, secret, sig, old_ts, tolerance=0)


def test_verify_with_rotation_primary():
    primary = generate_secret()
    secondary = generate_secret()
    payload = "test"
    sig, ts = sign(payload, primary)
    assert verify_with_rotation(payload, primary, secondary, sig, ts)


def test_verify_with_rotation_secondary():
    primary = generate_secret()
    secondary = generate_secret()
    payload = "test"
    sig, ts = sign(payload, secondary)
    assert verify_with_rotation(payload, primary, secondary, sig, ts)


def test_verify_with_rotation_neither():
    primary = generate_secret()
    secondary = generate_secret()
    unrelated = generate_secret()
    payload = "test"
    sig, ts = sign(payload, unrelated)
    assert not verify_with_rotation(payload, primary, secondary, sig, ts)


def test_verify_with_rotation_empty_secondary():
    primary = generate_secret()
    payload = "test"
    sig, ts = sign(payload, primary)
    assert verify_with_rotation(payload, primary, "", sig, ts)


def test_generate_secret_format():
    secret = generate_secret()
    assert secret.startswith("whsec_")
    assert len(secret) == 6 + 64


def test_sign_bytes_payload():
    secret = generate_secret()
    payload = b'{"event": "test"}'
    sig, ts = sign(payload, secret)
    assert verify(payload, secret, sig, ts)


def test_verify_string_timestamp():
    secret = generate_secret()
    payload = "test"
    sig, ts = sign(payload, secret)
    assert verify(payload, secret, sig, str(ts))


def test_sign_format():
    secret = generate_secret()
    sig, _ = sign("test", secret)
    assert sig.startswith("v1=")
    hex_part = sig[3:]
    assert len(hex_part) == 64
    int(hex_part, 16)


def test_verify_malformed_signature():
    secret = generate_secret()
    payload = "test"
    _, ts = sign(payload, secret)
    # Garbage signature, no v1= prefix
    assert not verify(payload, secret, "this-is-not-a-real-signature", ts)


def test_verify_missing_v1_prefix():
    secret = generate_secret()
    payload = "test"
    sig, ts = sign(payload, secret)
    # Strip v1= prefix entirely; should now be rejected
    raw = sig[3:]
    assert not verify(payload, secret, raw, ts)


def test_verify_future_skewed_timestamp():
    secret = generate_secret()
    payload = "test"
    future_ts = int(time.time()) + 600
    sig, _ = sign(payload, secret, future_ts)
    # Future timestamp beyond tolerance should be rejected
    assert not verify(payload, secret, sig, future_ts, tolerance=300)


def test_verify_far_future_timestamp_no_tolerance():
    secret = generate_secret()
    payload = "test"
    future_ts = int(time.time()) + 99999
    sig, _ = sign(payload, secret, future_ts)
    # With tolerance=0, signature only matters
    assert verify(payload, secret, sig, future_ts, tolerance=0)


def test_verify_multi_scheme_signature():
    secret = generate_secret()
    payload = "test"
    sig, ts = sign(payload, secret)
    # Multi-scheme header: prepend a fake v0 element
    multi = f"v0=deadbeef,{sig}"
    assert verify(payload, secret, multi, ts)


def test_verify_multi_scheme_signature_trailing():
    secret = generate_secret()
    payload = "test"
    sig, ts = sign(payload, secret)
    # v1 in middle/end, with whitespace
    multi = f"t={ts}, {sig} ,v0=foo"
    assert verify(payload, secret, multi, ts)


def test_verify_multi_scheme_no_v1():
    secret = generate_secret()
    payload = "test"
    _, ts = sign(payload, secret)
    # Multi-scheme header without v1
    multi = "v0=deadbeef,t=12345"
    assert not verify(payload, secret, multi, ts)


def test_verify_empty_signature():
    secret = generate_secret()
    payload = "test"
    _, ts = sign(payload, secret)
    assert not verify(payload, secret, "", ts)


def test_verify_invalid_timestamp_string():
    secret = generate_secret()
    payload = "test"
    sig, _ = sign(payload, secret)
    assert not verify(payload, secret, sig, "not-a-number")
