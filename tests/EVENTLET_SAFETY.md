# Eventlet Safety in Tests

## Overview

This test suite is protected against eventlet monkey-patching to prevent deadlocks and ensure reliable test execution.

## Key Safeguards

### 1. Automatic Protection
The `conftest.py` automatically:
- Disables eventlet monkey-patching via environment variable
- Prevents `eventlet.monkey_patch()` from running
- Warns if eventlet patches are detected at runtime

### 2. Available Fixtures

#### `mock_socketio`
Safe SocketIO mock that uses threading instead of eventlet:

```python
def test_websocket_feature(mock_socketio):
    # Use mock_socketio instead of real SocketIO
    mock_socketio.emit('event', {'data': 'test'})
    assert mock_socketio.async_mode == 'threading'  # Always threading
```

#### `app`
Test Flask app with no background workers:

```python
def test_route(app, client):
    # App is safely configured for testing
    response = client.get('/api/endpoint')
    assert response.status_code == 200
```

## What NOT to Do

❌ **Never** call `eventlet.monkey_patch()` in test files:

```python
# DON'T DO THIS IN TESTS
import eventlet
eventlet.monkey_patch()  # Will cause warnings and potential deadlocks
```

❌ **Never** import modules that auto-patch:

```python
# DON'T DO THIS
from gevent import monkey
monkey.patch_all()  # Similar issues to eventlet
```

## What TO Do

✅ **Use mock fixtures** for async operations:

```python
def test_async_operation(mock_socketio, mock_db):
    # All async operations are mocked
    result = perform_operation()
    assert result is not None
```

✅ **Mark tests that need real eventlet** (if absolutely necessary):

```python
@pytest.mark.slow
@pytest.mark.requires_eventlet
def test_real_eventlet_behavior():
    # This should be rare and well-documented
    pass
```

## Debugging Eventlet Issues

If you see this warning:

```
WARNING: eventlet has already monkey-patched socket. Tests may hang.
```

**Action**: Find and remove the `eventlet.monkey_patch()` call in your test files.

**Common locations**:
- Test file imports
- Conftest plugins
- Imported modules that auto-patch

## Verification

Check eventlet status:

```bash
python3 -c "
import sys
sys.path.insert(0, 'tests')
import conftest
import eventlet
print(f'Socket patched: {eventlet.patcher.is_monkey_patched(\"socket\")}')
"
# Expected output: Socket patched: False
```

## Architecture

### Threading Model
- **Tests**: Standard Python threading (no eventlet)
- **Mocks**: Use `MagicMock` for async operations
- **Flask app**: `TESTING=True` disables background workers

### Why This Matters
- **Pytest uses threads** for test collection and execution
- **Eventlet monkey-patches** replace threading with greenlets
- **Mixing both** causes deadlocks and hangs
- **Solution**: Keep eventlet isolated from test runner

## Related Files

- `tests/conftest.py`: Main safety implementation
- `PHASE2_STEP5_COMPLETE.md`: Detailed documentation of changes

## Questions?

If tests hang or show eventlet warnings:
1. Check for `monkey_patch()` calls
2. Verify `conftest.py` hasn't been modified
3. Run: `pytest -v -s` to see detailed output
4. Check the eventlet status verification above
